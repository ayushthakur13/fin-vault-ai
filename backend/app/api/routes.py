from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time

from app.core.retrieval import perform_hybrid_retrieval, build_llm_prompt
from app.core.embeddings import embed_text
from app.core.llm import quick_model_call, deep_model_call
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    mode: Optional[str] = None  # 'quick' or 'deep', overrides default
    tickers: Optional[list[str]] = None  # Filter to specific companies
    retrieval_mode: Optional[str] = None  # Force retrieval type: 'numeric', 'narrative', 'hybrid'


class QueryResponse(BaseModel):
    query: str
    analysis: str
    retrieval_mode: str
    model_used: str
    numeric_data_count: int
    narrative_chunks_count: int
    latency_ms: int
    tokens_used: Optional[int] = None


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/")
def root() -> dict:
    return {"service": "FinVault AI", "status": "ok"}


@router.post("/query", response_model=QueryResponse)
async def query_financial_data(payload: QueryRequest) -> QueryResponse:
    """
    Execute financial query with hybrid retrieval + LLM reasoning
    
    Workflow:
    1. Classify query or use forced retrieval mode
    2. Retrieve numeric metrics from PostgreSQL
    3. Retrieve narrative chunks from Qdrant (if applicable)
    4. Send combined context to Groq LLM
    5. Return structured response
    """
    try:
        start_time = time.time()
        
        # Validate query
        if not payload.query or len(payload.query.strip()) < 5:
            raise HTTPException(status_code=400, detail="Query must be at least 5 characters")
        
        logger.info(f"Processing query: {payload.query[:100]}...")
        
        # Perform hybrid retrieval
        context = perform_hybrid_retrieval(
            query=payload.query,
            embeddings_model_fn=embed_text,
            tickers=payload.tickers,
            force_mode=payload.retrieval_mode,
            numeric_limit=50,
            narrative_limit=5
        )
        
        # Build LLM prompt with retrieved context
        llm_prompt = build_llm_prompt(
            query=payload.query,
            context=context,
            system_role="financial research assistant providing insights on company performance and market trends"
        )
        
        # Call LLM (select model based on mode)
        use_deep_mode = payload.mode == "deep"
        model_call_fn = deep_model_call if use_deep_mode else quick_model_call
        model_used = "llama-3.3-70b-versatile" if use_deep_mode else "llama-3.1-8b-instant"
        
        logger.info(f"Calling {model_used} for analysis...")
        llm_result = model_call_fn(llm_prompt)
        
        # Extract response
        analysis = llm_result.get("output", "No response generated")
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        retrieval_summary = context.get('retrieval_summary', {})
        
        return QueryResponse(
            query=payload.query,
            analysis=analysis,
            retrieval_mode=retrieval_summary.get('query_mode', 'unknown'),
            model_used=model_used,
            numeric_data_count=retrieval_summary.get('numeric_retrieved', 0),
            narrative_chunks_count=retrieval_summary.get('narrative_retrieved', 0),
            latency_ms=latency_ms,
            tokens_used=None  # Would need token counting from Groq response
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Query processing failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(exc)}")
