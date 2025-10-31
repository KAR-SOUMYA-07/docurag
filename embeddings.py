"""
Embeddings module using sentence-transformers
Uses all-MiniLM-L6-v2 model for generating text embeddings
Model is cached locally in models/ folder
"""

import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Model configuration
MODELS_DIR = os.getenv('MODELS_DIR', 'models')
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

class EmbeddingModel:
    """Wrapper for sentence transformer embedding model"""
    
    def __init__(self):
        """Initialize the embedding model"""
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load or download the embedding model"""
        try:
            print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            
            # Create models directory if it doesn't exist
            os.makedirs(MODELS_DIR, exist_ok=True)
            
            # Load model with local cache
            self.model = SentenceTransformer(
                EMBEDDING_MODEL_NAME,
                cache_folder=MODELS_DIR
            )
            
            print(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
            
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            show_progress: Show progress bar
        
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()

# Global embedding model instance
_embedding_model = None

def get_embedding_model() -> EmbeddingModel:
    """Get or create global embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model

def embed_text(text: str) -> np.ndarray:
    """Convenience function to embed a single text"""
    model = get_embedding_model()
    return model.embed_text(text)

def embed_texts(texts: List[str], show_progress: bool = True) -> np.ndarray:
    """Convenience function to embed multiple texts"""
    model = get_embedding_model()
    return model.embed_texts(texts, show_progress)

if __name__ == '__main__':
    # Test the embedding model
    print("Testing embedding model...")
    
    test_texts = [
        "This is a test sentence.",
        "Another test sentence for embedding.",
        "Machine learning is fascinating."
    ]
    
    model = get_embedding_model()
    print(f"\nEmbedding dimension: {model.get_embedding_dimension()}")
    
    # Test single embedding
    print("\nTesting single text embedding...")
    embedding = embed_text(test_texts[0])
    print(f"Embedding shape: {embedding.shape}")
    print(f"First 10 values: {embedding[:10]}")
    
    # Test batch embedding
    print("\nTesting batch embedding...")
    embeddings = embed_texts(test_texts)
    print(f"Embeddings shape: {embeddings.shape}")
    
    print("\nEmbedding test completed successfully!")
