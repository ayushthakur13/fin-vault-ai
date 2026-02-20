from typing import Optional, Dict, List, Any
from qdrant_client import QdrantClient

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client, raises error if QDRANT_URL not configured"""
    if not settings.qdrant_url:
        logger.error("QDRANT_URL not configured - Qdrant features unavailable")
        raise ValueError("QDRANT_URL environment variable not set")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


def test_qdrant_connection() -> bool:
    """Test Qdrant connection and availability"""
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception as exc:
        logger.warning("Qdrant connection failed: %s", exc)
        return False


def search_narrative(
    query_embedding: List[float],
    collection_name: str = "financial_narratives",
    tickers: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    doc_types: Optional[List[str]] = None,
    top_k: int = 5,
    score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search narrative data in Qdrant using semantic similarity.
    
    Retrieves narrative chunks (transcript excerpts, 10-K sections, etc) relevant
    to a query embedding, with optional filtering by company, year, or document type.
    Gracefully returns empty list if Qdrant unavailable or collection missing.
    
    Args:
        query_embedding: Vector embedding of user query (e.g., from embed_text)
        collection_name: Qdrant collection to search (default: financial_narratives)
        tickers: Filter by stock tickers (e.g., ['AAPL', 'MSFT'])
        years: Filter by fiscal years (e.g., [2025, 2024])
        doc_types: Filter by document type (e.g., ['earnings_transcript', 'risk_factors'])
        top_k: Number of results to return (default 5, capped at 10 for safety)
        score_threshold: Minimum similarity score (0.0-1.0, default 0.5)
        
    Returns:
        List of narrative chunk dicts with keys:
        - point_id: Unique Qdrant point ID
        - text: Narrative chunk text (max 500 chars)
        - metadata: Dict with company, ticker, year, doc_type, section_title
        - similarity_score: Cosine similarity score (0.0-1.0)
    """
    # DEFENSIVE: Sanitize parameters
    top_k = min(max(top_k, 1), 10)  # Cap between 1 and 10
    score_threshold = max(0.0, min(score_threshold, 1.0))  # Clamp 0-1
    
    # DEFENSIVE: Handle Qdrant unavailability gracefully
    try:
        client = get_qdrant_client()
    except ValueError as exc:
        logger.warning(f"Qdrant unavailable: {exc}")
        return []
    except Exception as exc:
        logger.error(f"Qdrant client failed: {exc}")
        return []
    
    try:
        # DEFENSIVE: Verify collection exists before search
        try:
            collection_info = client.get_collection(collection_name)
            logger.debug(f"Searching collection '{collection_name}' ({collection_info.points_count} points)")
        except Exception as exc:
            logger.warning(f"Collection '{collection_name}' not found - narrative search unavailable")
            return []
        
        # Build query filter - simplified to avoid Qdrant API complexity
        # In production, these filters should be indexed in Qdrant for performance
        filters = None
        # Note: Complex filtering deferred - results are post-filtered in Python if needed
        
        # Search Qdrant using search_points API
        try:
            search_result = client.search_points(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=filters,
                score_threshold=score_threshold
            )
            # Extract points from SearchResponse
            search_results = search_result.points if hasattr(search_result, 'points') else search_result
        except Exception as search_exc:
            logger.warning(f"Narrative search failed: {search_exc}")
            return []
        
        # Format results with post-filtering
        results = []
        for result in search_results:
            payload = result.payload or {}
            
            # Post-filter by tickers, years, doc_types if specified
            if tickers and payload.get('ticker', '').upper() not in [t.upper() for t in tickers]:
                continue
            if years and payload.get('year', 0) not in years:
                continue
            if doc_types and payload.get('doc_type', 'unknown') not in doc_types:
                continue
            
            results.append({
                'point_id': result.id,
                'text': payload.get('summary', '')[:500],  # First 500 chars as preview
                'metadata': {
                    'company': payload.get('company', 'Unknown'),
                    'ticker': payload.get('ticker', 'Unknown'),
                    'year': payload.get('year', 0),
                    'doc_type': payload.get('doc_type', 'unknown'),
                    'section_title': payload.get('section_title', ''),
                    'chunk_id': payload.get('chunk_id', 0),
                },
                'similarity_score': result.score or 0.0
            })
        
        logger.debug(f"Found {len(results)} narrative chunks for query (post-filtered)")
        return results
        
    except Exception as exc:
        logger.error(f"Narrative search failed: {exc}")
        return []
