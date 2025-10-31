"""
RAG (Retrieval-Augmented Generation) Pipeline
Handles query processing, vector search, and Groq API integration
"""

import os
from typing import List, Dict, Optional
from groq import Groq
from embeddings import embed_text
from vector_store import SessionVectorStore

# Groq configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')

class RAGPipeline:
    """RAG pipeline for question answering"""
    
    def __init__(self):
        """Initialize RAG pipeline"""
        self.groq_client = None
        self.vector_manager = SessionVectorStore()
        self.initialize_groq()
    
    def initialize_groq(self):
        """Initialize Groq client"""
        if not GROQ_API_KEY or GROQ_API_KEY == 'your_groq_api_key_here':
            print("WARNING: GROQ_API_KEY not set. Please add it to .env file")
            return
        
        try:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
            print("Groq client initialized successfully")
        except Exception as e:
            print(f"Error initializing Groq client: {e}")
    
    def retrieve_context(self, query: str, session_id: str, k: int = 5) -> List[Dict]:
        """
        Retrieve relevant context from vector store
        
        Args:
            query: User query
            session_id: Chat session ID
            k: Number of chunks to retrieve
        
        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Get vector store for session
            vector_store = self.vector_manager.get_or_create_store(session_id)
            
            # Check if store has documents
            if len(vector_store.chunks) == 0:
                return []
            
            # Embed query
            query_embedding = embed_text(query)
            
            # Search for similar chunks
            results = vector_store.search(query_embedding, k=k)
            
            return results
        
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def generate_prompt(self, query: str, context_chunks: List[Dict], conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Generate prompt for LLM with retrieved context and conversation history
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        
        Returns:
            Formatted prompt
        """
        # Build conversation context
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            # Get last 6 messages (3 exchanges) for context
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            conversation_context = "Previous conversation:\n"
            for msg in recent_history:
                role_label = "User" if msg['role'] == 'user' else "Assistant"
                conversation_context += f"{role_label}: {msg['content']}\n"
            conversation_context += "\n"
        
        if not context_chunks:
            # No context available
            prompt = f"""You are DocuSensei, an intelligent document assistant. 

{conversation_context}Current User Query: {query}

Instructions:
- Remember and use information from the previous conversation
- If the user mentioned their name or other personal details earlier, remember them
- If no documents are uploaded, provide helpful general assistance
- Be conversational and maintain context from previous messages

Answer:"""
        else:
            # Format context from documents
            context_text = "\n\n".join([
                f"[Source: {chunk['metadata'].get('filename', 'unknown')}]\n{chunk['chunk']}"
                for chunk in context_chunks
            ])
            
            prompt = f"""You are DocuSensei, an intelligent document assistant. Answer the user's question based on both the provided document context AND the conversation history.

Context from documents:
{context_text}

{conversation_context}Current User Query: {query}

Instructions:
- Answer based on BOTH the document context AND the conversation history
- Remember information the user shared in previous messages (like their name, preferences, etc.)
- If the user mentioned something earlier in the conversation, acknowledge and use that information
- If the context doesn't contain enough information, say so clearly
- Be concise, accurate, and conversational
- Cite the source document when relevant
- Maintain context across the conversation

Answer:"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using Groq API
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            Generated response
        """
        if not self.groq_client:
            return "Error: Groq API is not configured. Please add GROQ_API_KEY to .env file."
        
        try:
            # Call Groq API
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are DocuSensei, a helpful and intelligent document assistant. Provide clear, accurate answers based on the provided context.You are designed by Docusensei Team[You have no relation with openAI or gpt-4o]"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=GROQ_MODEL,
                temperature=0.9,
                max_tokens=2048,
                top_p=0.9,
            )
            
            response = chat_completion.choices[0].message.content
            return response
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def query(self, question: str, session_id: str, conversation_history: Optional[List[Dict]] = None, k: int = 5) -> Dict:
        """
        Process a query with conversation history
        
        Args:
            question: User's question
            session_id: Chat session ID
            conversation_history: Previous messages in the conversation
            k: Number of document chunks to retrieve
        
        Returns:
            Dict with answer, context chunks, and metadata
        """
        # Retrieve context from documents
        context_chunks = self.retrieve_context(question, session_id, k)
        
        # Generate prompt with conversation history
        prompt = self.generate_prompt(question, context_chunks, conversation_history)
        
        # Generate response
        answer = self.generate_response(prompt)
        
        return {
            'answer': answer,
            'context_chunks': context_chunks,
            'num_chunks_used': len(context_chunks)
        }

# Global RAG pipeline instance
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

if __name__ == '__main__':
    # Test RAG pipeline
    print("Testing RAG pipeline...")
    
    pipeline = get_rag_pipeline()
    
    test_query = "What is machine learning?"
    test_session = "test_session"
    
    result = pipeline.query(test_query, test_session)
    
    print(f"\nQuery: {test_query}")
    print(f"Answer: {result['answer']}")
    print(f"Chunks used: {result['num_chunks_used']}")
