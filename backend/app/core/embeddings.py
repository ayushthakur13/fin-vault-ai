"""
Embeddings Module
Lazy-loads sentence-transformers for semantic search
Handles query and document embedding with caching
"""
from typing import Optional
import os

from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Global model cache
_embedding_model = None


def get_embedding_model():
    """
    Lazy-load and cache embedding model (BGE-small or similar)
    
    Returns:
        Loaded embedding model or None if unavailable
    """
    global _embedding_model
    
    if _embedding_model is not None:
        return _embedding_model
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        logger.info(f"Loading embedding model: {model_name}")
        
        _embedding_model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")
        
        return _embedding_model
        
    except ImportError:
        logger.warning("sentence_transformers not installed, embeddings unavailable")
        return None
    except Exception as exc:
        logger.error(f"Failed to load embedding model: {exc}")
        return None


def embed_text(text: str) -> Optional[list[float]]:
    """
    Embed text using cached model
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector or None
    """
    if not text or not isinstance(text, str):
        return None
    
    try:
        model = get_embedding_model()
        if model is None:
            logger.debug("Embedding model not available, skipping embedding")
            return None
        
        embedding = model.encode(text.strip(), convert_to_tensor=False)
        return embedding.tolist()
        
    except Exception as exc:
        logger.error(f"Failed to embed text: {exc}")
        return None


def embed_batch(texts: list[str]) -> Optional[list[list[float]]]:
    """
    Embed multiple texts efficiently via batch processing
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return None
    
    try:
        model = get_embedding_model()
        if model is None:
            return None
        
        embeddings = model.encode(texts, convert_to_tensor=False)
        return [emb.tolist() for emb in embeddings]
        
    except Exception as exc:
        logger.error(f"Failed to embed batch: {exc}")
        return None


def get_model_dimension() -> int:
    """
    Get embedding model dimension for Qdrant collection creation
    
    Returns:
        Vector size (typically 384 for BGE-small)
    """
    try:
        model = get_embedding_model()
        if model is None:
            return 384  # Default for BGE-small
        
        # Get dimension from model
        test_embedding = model.encode("test")
        return len(test_embedding)
        
    except Exception:
        return 384
