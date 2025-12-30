"""
Embedding Generator Agent
Generates text embeddings for semantic memory and similarity search
"""
import numpy as np
from typing import List, Union
from config import Config

# Try to import sentence transformers, fallback to simple embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Using fallback embeddings.")


class EmbeddingGenerator:
    def __init__(self, lazy_load: bool = True):
        self._model = None
        self._model_loaded = False
        self._lazy_load = lazy_load
        self.dimension = 384  # Default dimension for all-MiniLM-L6-v2
        
        if not lazy_load and EMBEDDINGS_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load the embedding model (called lazily on first use)"""
        if self._model_loaded:
            return
            
        if EMBEDDINGS_AVAILABLE:
            try:
                self._model = SentenceTransformer(Config.EMBEDDING_MODEL)
                print(f"Loaded embedding model: {Config.EMBEDDING_MODEL}")
            except Exception as e:
                print(f"Error loading embedding model: {e}")
        
        self._model_loaded = True
    
    @property
    def model(self):
        """Lazy-load model on first access"""
        if not self._model_loaded:
            self._load_model()
        return self._model
    
    def generate(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single string or list of strings
        
        Returns:
            Embedding vector(s) as list of floats
        """
        if self.model:
            embeddings = self.model.encode(text)
            if isinstance(text, str):
                return embeddings.tolist()
            return [e.tolist() for e in embeddings]
        else:
            # Fallback: simple hash-based embedding (for demo purposes)
            return self._fallback_embed(text)
    
    def _fallback_embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Simple fallback embedding using character frequencies"""
        def embed_single(s: str) -> List[float]:
            # Create a simple embedding based on character frequencies
            s = s.lower()
            vec = [0.0] * self.dimension
            for i, char in enumerate(s):
                idx = ord(char) % self.dimension
                vec[idx] += 1.0 / (i + 1)
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = [v / norm for v in vec]
            return vec
        
        if isinstance(text, str):
            return embed_single(text)
        return [embed_single(t) for t in text]
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_similar(self, query_embedding: List[float], 
                     embeddings: List[List[float]], 
                     top_k: int = 5) -> List[tuple]:
        """
        Find most similar embeddings
        
        Args:
            query_embedding: The query vector
            embeddings: List of embeddings to search
            top_k: Number of results to return
        
        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []
        for i, emb in enumerate(embeddings):
            sim = self.similarity(query_embedding, emb)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Global embedding generator instance with lazy loading
embedding_generator = EmbeddingGenerator(lazy_load=True)
