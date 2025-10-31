# DocuSensei Backend Setup - Complete!

## ✅ What's Been Created

### 1. Database Module (`database.py`)
- SQLite database with tables for: chat_sessions, messages, uploaded_files
- Functions to create/read/update/delete sessions
- Message storage and retrieval
- File tracking per session

### 2. PDF Processor (`pdf_processor.py`)
- Extracts text from PDF, TXT, DOCX, DOC files
- Chunks text into overlapping segments (500 chars, 50 overlap)
- Smart boundary detection (sentences/words)

### 3. Embeddings Module (`embeddings.py`)
- Uses `sentence-transformers/all-MiniLM-L6-v2` model
- Downloads model to `models/` folder (cached locally)
- Generates 384-dimensional embeddings
- Batch processing support

### 4. Vector Store (`vector_store.py`)
- FAISS-CPU for fast similarity search
- Session-specific vector stores
- Saves/loads from disk
- Metadata tracking for each chunk

### 5. RAG Pipeline (`rag_pipeline.py`)
- Query embedding generation
- Vector similarity search (retrieves top K chunks)
- Prompt generation with retrieved context
- Groq API integration for LLM responses

### 6. Flask Backend (`app.py`)
Complete routes:
- `POST /upload` - Process and embed documents
- `POST /chat` - RAG-based question answering
- `GET /history` - Get all chat sessions
- `GET /session/<id>` - Get messages for session
- `POST /session/create` - Create new session
- `DELETE /session/<id>` - Delete session
- `POST /clear-all` - Clear all chats

## 📋 Next Steps

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

This will install:
- Flask, Werkzeug
- sentence-transformers (includes torch)
- faiss-cpu
- PyPDF2, python-docx
- groq
- python-dotenv

### Step 2: Configure .env File
Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama3-8b-8192
```

Get API key from: https://console.groq.com/keys

### Step 3: Update Frontend (script.js)
The frontend needs updates to:
1. Send session_id with file uploads
2. Send queries to /chat endpoint with session_id
3. Display messages in ChatGPT style (user right, bot left)
4. Load chat history from /history endpoint
5. Handle session switching
6. Implement "Clear All" button

### Step 4: Test the Pipeline
1. Start server: `python app.py`
2. First run will download the embedding model (~90MB) to `models/` folder
3. Upload a document
4. Ask questions about it
5. Check that responses use document context

## 🏗️ How It Works

### File Upload Flow:
1. User uploads file → Frontend sends to `/upload` with session_id
2. Backend extracts text → chunks it → generates embeddings
3. Embeddings stored in FAISS vector store
4. File metadata saved to SQLite database
5. Success response sent to frontend

### Chat Flow:
1. User sends message → Frontend sends to `/chat` with session_id
2. Backend embeds the query
3. Searches vector store for relevant chunks (top 5)
4. Builds prompt with retrieved context
5. Sends to Groq API for answer generation
6. Saves user message + bot response to database
7. Returns answer to frontend

### Session Management:
- Each "New Chat" creates a unique session_id
- Sessions have their own vector store
- Chat history persists in SQLite
- Can load previous chats from sidebar

## 🎨 Frontend TODO

Update `static/script.js` to:

1. **Track current session:**
```javascript
let currentChatId = Date.now().toString();
```

2. **Send session_id with uploads:**
```javascript
formData.append('session_id', currentChatId);
```

3. **Update sendMessage() function:**
```javascript
fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: userInput,
        session_id: currentChatId
    })
})
.then(response => response.json())
.then(data => {
    addMessage(data.response, 'bot');
});
```

4. **Display messages ChatGPT style:**
- User messages: right-aligned, blue background
- Bot messages: left-aligned, gray background

5. **Load chat history on page load:**
```javascript
fetch('/history')
.then(response => response.json())
.then(data => {
    renderChatHistory(data.sessions);
});
```

6. **Add "Clear All Chats" button** that calls `/clear-all`

## 🚀 Ready to Run!

All backend components are complete and integrated. The pipeline is:
**Upload → Extract → Chunk → Embed → Store → Query → Retrieve → Generate → Display**

Just install dependencies, configure .env, and update the frontend!
