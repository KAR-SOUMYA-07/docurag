"""
FAISS Vector Store for document embeddings
Handles storage, retrieval, and similarity search
"""

import os
import pickle
from typing import List, Tuple, Dict, Optional
import numpy as np
import faiss

class VectorStore:
    """FAISS-based vector store for document chunks"""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize vector store
        
        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks = []  # Store original text chunks
        self.metadata = []  # Store metadata (filename, chunk_id, etc.)
        
    def add_documents(self, embeddings: np.ndarray, chunks: List[str], metadata: List[Dict]):
        """
        Add documents to vector store
        
        Args:
            embeddings: Document embeddings (n_docs, dimension)
            chunks: Original text chunks
            metadata: Metadata for each chunk
        """
        if len(embeddings) != len(chunks) or len(embeddings) != len(metadata):
            raise ValueError("Embeddings, chunks, and metadata must have same length")
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store chunks and metadata
        self.chunks.extend(chunks)
        self.metadata.extend(metadata)
        
        print(f"Added {len(embeddings)} documents. Total: {len(self.chunks)}")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding
            k: Number of results to return
        
        Returns:
            List of dicts with 'chunk', 'metadata', 'score'
        """
        if len(self.chunks) == 0:
            return []
        
        # Ensure k doesn't exceed available documents
        k = min(k, len(self.chunks))
        
        # Search
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.chunks):  # Valid index
                results.append({
                    'chunk': self.chunks[idx],
                    'metadata': self.metadata[idx],
                    'score': float(dist),
                    'rank': i + 1
                })
        
        return results
    
    def save(self, file_path: str):
        """Save vector store to disk"""
        # Save FAISS index
        faiss.write_index(self.index, f"{file_path}.faiss")
        
        # Save chunks and metadata
        with open(f"{file_path}.pkl", 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'dimension': self.dimension
            }, f)
        
        print(f"Vector store saved to {file_path}")
    
    def load(self, file_path: str):
        """Load vector store from disk"""
        # Load FAISS index
        self.index = faiss.read_index(f"{file_path}.faiss")
        
        # Load chunks and metadata
        with open(f"{file_path}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
            self.dimension = data['dimension']
        
        print(f"Vector store loaded from {file_path}. Total documents: {len(self.chunks)}")
    
    def clear(self):
        """Clear all data from vector store"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.metadata = []
        print("Vector store cleared")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': len(self.chunks),
            'dimension': self.dimension,
            'index_type': type(self.index).__name__
        }

class SessionVectorStore:
    """Manager for session-specific vector stores"""
    
    def __init__(self, base_dir: str = 'data/vector_stores'):
        """Initialize session vector store manager"""
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.stores = {}  # Cache loaded stores
    
    def get_store_path(self, session_id: str) -> str:
        """Get file path for session vector store"""
        return os.path.join(self.base_dir, f"session_{session_id}")
    
    def get_or_create_store(self, session_id: str, dimension: int = 384) -> VectorStore:
        """Get existing or create new vector store for session"""
        if session_id in self.stores:
            return self.stores[session_id]
        
        store = VectorStore(dimension)
        store_path = self.get_store_path(session_id)
        
        # Try to load existing store
        if os.path.exists(f"{store_path}.faiss"):
            try:
                store.load(store_path)
            except Exception as e:
                print(f"Error loading vector store: {e}. Creating new one.")
        
        self.stores[session_id] = store
        return store
    
    def save_store(self, session_id: str):
        """Save vector store for session"""
        if session_id in self.stores:
            store_path = self.get_store_path(session_id)
            self.stores[session_id].save(store_path)
    
    def delete_store(self, session_id: str):
        """Delete vector store for session"""
        store_path = self.get_store_path(session_id)
        
        # Remove from cache
        if session_id in self.stores:
            del self.stores[session_id]
        
        # Delete files
        for ext in ['.faiss', '.pkl']:
            file_path = f"{store_path}{ext}"
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")

if __name__ == '__main__':
    # Test vector store
    print("Testing FAISS vector store...")
    
    # Create dummy embeddings
    dimension = 384
    n_docs = 10
    embeddings = np.random.rand(n_docs, dimension).astype('float32')
    chunks = [f"This is test chunk {i}" for i in range(n_docs)]
    metadata = [{'chunk_id': i, 'source': 'test.pdf'} for i in range(n_docs)]
    
    # Create and populate store
    store = VectorStore(dimension)
    store.add_documents(embeddings, chunks, metadata)
    
    # Test search
    query_embedding = np.random.rand(dimension).astype('float32')
    results = store.search(query_embedding, k=3)
    
    print(f"\nSearch results:")
    for result in results:
        print(f"  Rank {result['rank']}: {result['chunk']} (score: {result['score']:.4f})")
    
    # Test save/load
    store.save('test_store')
    
    new_store = VectorStore(dimension)
    new_store.load('test_store')
    print(f"\nLoaded store stats: {new_store.get_stats()}")
    
    # Cleanup
    import os
    os.remove('test_store.faiss')
    os.remove('test_store.pkl')
    
    print("\nVector store test completed!")
