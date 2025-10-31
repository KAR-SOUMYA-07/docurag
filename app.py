from flask import Flask, render_template, request, jsonify
import os
import time
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
import database as db
from pdf_processor import process_document, chunk_text
from embeddings import get_embedding_model, embed_texts
from vector_store import SessionVectorStore
from rag_pipeline import get_rag_pipeline

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/temp'
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'doc', 'docx'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Initialize database
db.init_db()

# Global instances
embedding_model = None
vector_manager = None
rag_pipeline = None

def init_models():
    """Initialize models on first request"""
    global embedding_model, vector_manager, rag_pipeline
    if embedding_model is None:
        print("Initializing models...")
        embedding_model = get_embedding_model()
        vector_manager = SessionVectorStore()
        rag_pipeline = get_rag_pipeline()
        print("Models initialized successfully!")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/<session_id>')
def session_view(session_id):
    """View specific session - render same page, JS will load the session"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    init_models()
    
    # Get session ID and file
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, TXT, DOC, DOCX'}), 400
    
    try:
        start_time = time.time()
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(filepath)
        
        # Process document - extract text
        print(f"Processing document: {filename}")
        text = process_document(filepath)
        
        if not text:
            os.remove(filepath)
            return jsonify({'error': 'Could not extract text from document'}), 400
        
        print(f"Extracted {len(text)} characters from {filename}")
        
        # Split into chunks
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        print(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = embed_texts(chunks, show_progress=False)
        print(f"Generated embeddings with shape: {embeddings.shape}")
        
        # Create metadata for each chunk
        metadata = [
            {
                'filename': filename,
                'chunk_id': i,
                'session_id': session_id
            }
            for i in range(len(chunks))
        ]
        
        # Get or create vector store for this session
        vector_store = vector_manager.get_or_create_store(session_id)
        
        # Add documents to vector store
        vector_store.add_documents(embeddings, chunks, metadata)
        
        # Save vector store
        vector_manager.save_store(session_id)
        
        # Save file record to database
        db.add_uploaded_file(session_id, filename, filepath, vector_store_id=session_id)
        
        # Ensure minimum 3 seconds for animation
        elapsed_time = time.time() - start_time
        if elapsed_time < 3:
            time.sleep(3 - elapsed_time)
        
        print(f"File {filename} processed successfully in {time.time() - start_time:.2f}s")
        
        return jsonify({
            'success': True,
            'message': f'File "{filename}" processed successfully',
            'filename': filename,
            'num_chunks': len(chunks),
            'text_length': len(text)
        })
    
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with RAG"""
    init_models()
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        if not user_message or not session_id:
            return jsonify({'error': 'Message and session_id are required'}), 400
        
        print(f"Processing query: {user_message} for session: {session_id}")
        
        # Get conversation history from database (before adding current message)
        messages = db.get_messages(session_id)
        conversation_history = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
        ]
        
        # Save user message to database
        db.add_message(session_id, 'user', user_message)
        
        # Use RAG pipeline to generate response with conversation history
        result = rag_pipeline.query(user_message, session_id, conversation_history=conversation_history, k=5)
        
        bot_response = result['answer']
        num_chunks = result['num_chunks_used']
        
        # Save bot response to database
        db.add_message(session_id, 'assistant', bot_response)
        
        print(f"Generated response using {num_chunks} chunks and {len(conversation_history)} previous messages")
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'num_chunks_used': num_chunks
        })
    
    except Exception as e:
        print(f"Error in chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get all chat sessions"""
    try:
        sessions = db.get_all_chat_sessions()
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get messages for a specific session"""
    try:
        messages = db.get_messages(session_id)
        files = db.get_session_files(session_id)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'files': files
        })
    except Exception as e:
        print(f"Error getting session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/session/create', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        title = data.get('title', 'New Chat')
        
        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
        
        db.create_chat_session(session_id, title)
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        # Delete from database
        db.delete_chat_session(session_id)
        
        # Delete vector store
        if vector_manager:
            vector_manager.delete_store(session_id)
        
        # Delete uploaded files
        files = db.get_session_files(session_id)
        for file_record in files:
            file_path = file_record['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Session deleted'
        })
    except Exception as e:
        print(f"Error deleting session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-all', methods=['POST'])
def clear_all():
    """Clear all chat sessions"""
    try:
        # Get all sessions
        sessions = db.get_all_chat_sessions()
        
        # Delete vector stores and files for each session
        for session in sessions:
            session_id = session['id']
            if vector_manager:
                vector_manager.delete_store(session_id)
            
            # Delete uploaded files
            files = db.get_session_files(session_id)
            for file_record in files:
                file_path = file_record['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Clear database
        db.clear_all_chats()
        
        return jsonify({
            'success': True,
            'message': 'All chats cleared'
        })
    except Exception as e:
        print(f"Error clearing all chats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting DocuSensei server...")
    print("Initializing models (this may take a moment on first run)...")
    init_models()
    print("Server ready!")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, reloader_type='stat')

