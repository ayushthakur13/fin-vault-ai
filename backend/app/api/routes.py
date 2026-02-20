from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time

from app.core.retrieval import (
    perform_hybrid_retrieval,
    build_llm_prompt,
    assemble_context,
    detect_contradictions,
    classify_query_mode
)
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


class SourceReference(BaseModel):
    doc_type: str
    ticker: str
    year: int
    section: Optional[str] = None
    similarity_score: Optional[float] = None


class QueryResponse(BaseModel):
    query: str
    analysis: str
    retrieval_mode: str
    model_used: str
    numeric_data_count: int
    narrative_chunks_count: int
    sources: List[SourceReference] = []
    latency_ms: int
    tokens_used: Optional[int] = None
    contradictions_detected: Optional[str] = None


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/")
def root() -> dict:
    return {"service": "FinVault AI", "status": "ok"}


@router.post("/query", response_model=QueryResponse)
async def query_financial_data(payload: QueryRequest) -> QueryResponse:
    """
    Execute financial query with hybrid retrieval + LLM reasoning.
    
    Phase 2 Hybrid Retrieval Workflow:
    1. Classify query intent (numeric, narrative, or hybrid)
    2. Retrieve numeric metrics from PostgreSQL if applicable
    3. Retrieve narrative chunks from Qdrant if applicable
    4. Assemble citation-rich context for LLM
    5. Detect contradictions between metrics and narrative
    6. Generate analysis with grounded citations
    
    DEFENSIVE: Graceful degradation if components fail.
    - Missing numeric data? Continue with narrative only
    - Missing narrative data? Continue with numeric only
    - LLM timeout? Return available data with error message
    - Contradiction detection fails? Proceed without it (non-blocking)
    """
    try:
        start_time = time.time()
        
        # DEFENSIVE: Validate query
        if not payload.query or len(payload.query.strip()) < 5:
            raise HTTPException(status_code=400, detail="Query must be at least 5 characters")
        
        logger.info(f"Processing query: {payload.query[:100]}...")
        
        # DEFENSIVE: Classify query mode with fallback
        try:
            query_mode = payload.retrieval_mode or classify_query_mode(payload.query)
        except Exception as exc:
            logger.warning(f"Query mode classification failed, defaulting to hybrid: {exc}")
            query_mode = "hybrid"
        logger.info(f"Detected query mode: {query_mode}")
        
        # DEFENSIVE: Perform hybrid retrieval (non-blocking per component)
        context = perform_hybrid_retrieval(
            query=payload.query,
            embeddings_model_fn=embed_text,
            tickers=payload.tickers,
            force_mode=payload.retrieval_mode,
            numeric_limit=50,
            narrative_limit=5
        )
        
        # Extract data with safety checks
        numeric_data = context.get('numeric_data', []) or []
        narrative_chunks = context.get('narrative_chunks', []) or []
        retrieval_summary = context.get('retrieval_summary', {})
        
        # DEFENSIVE: Validate we have at least some data
        if not numeric_data and not narrative_chunks:
            logger.warning("No retrieval data available")
            # Continue anyway - LLM can still generate response
        
        # DEFENSIVE: Build sources list with validation
        sources = []
        for chunk in narrative_chunks:
            try:
                if isinstance(chunk, dict):
                    sources.append(SourceReference(
                        doc_type=chunk.get('doc_type', 'unknown'),
                        ticker=chunk.get('ticker', 'unknown'),
                        year=chunk.get('year', 0),
                        section=chunk.get('section_title'),
                        similarity_score=chunk.get('score', 0.0)
                    ))
            except Exception as source_exc:
                logger.warning(f"Failed to build source reference: {source_exc}")
                continue
        
        # DEFENSIVE: Assemble context with error handling
        try:
            assembled_context = assemble_context(
                query=payload.query,
                numeric_data=numeric_data,
                narrative_chunks=[
                    {
                        'text': c.get('text', ''),
                        'metadata': {
                            'ticker': c.get('ticker', ''),
                            'year': c.get('year', 0),
                            'doc_type': c.get('doc_type', ''),
                            'section_title': c.get('section_title', ''),
                        },
                        'similarity_score': c.get('score', 0.0)
                    }
                    for c in narrative_chunks
                    if isinstance(c, dict)
                ],
                include_contradiction_check=True
            )
        except Exception as context_exc:
            logger.warning(f"Context assembly failed: {context_exc}")
            # Fallback: create minimal context
            assembled_context = f"Query: {payload.query}\n\nAnalyze the following financial inquiry."
        
        # Build LLM prompt
        llm_prompt = assembled_context + "\n\nProvide your financial analysis below:\n"
        
        # DEFENSIVE: Call LLM with timeout/error handling
        use_deep_mode = payload.mode == "deep"
        model_call_fn = deep_model_call if use_deep_mode else quick_model_call
        model_used = "llama-3.3-70b-versatile" if use_deep_mode else "llama-3.1-8b-instant"
        
        logger.info(f"Calling {model_used} for analysis...")
        analysis = "Unable to generate analysis"
        tokens_used = None
        
        try:
            llm_result = model_call_fn(llm_prompt)
            if isinstance(llm_result, dict):
                analysis = llm_result.get("output", "Unable to generate analysis")
                tokens_used = llm_result.get("tokens_used")
            else:
                analysis = str(llm_result or "Unable to generate analysis")
                
            # DEFENSIVE: Cap analysis length
            analysis = analysis[:5000] if analysis else "Unable to generate analysis"
            
        except Exception as llm_exc:
            logger.error(f"LLM call failed: {llm_exc}")
            # Graceful degradation: return what we have
            if numeric_data or narrative_chunks:
                analysis = "Analysis unavailable due to LLM service error. Retrieved data: " + \
                          f"{len(numeric_data)} metrics, {len(narrative_chunks)} narrative excerpts"
            else:
                analysis = "Unable to process query: retrieval and LLM generation both failed"
        
        # DEFENSIVE: Detect contradictions (non-blocking, Area #8)
        contradictions = None
        if retrieval_summary.get('query_mode') in ['hybrid', 'narrative'] and numeric_data and narrative_chunks:
            try:
                numeric_summary = "\n".join([
                    f"{m.get('ticker', '?')} - Revenue: ${m.get('revenue', 0)/1e9:.1f}B, NI: ${m.get('net_income', 0)/1e9:.1f}B"
                    for m in numeric_data[:5]
                ])
                narrative_summary = "\n".join([
                    c.get('text', '')[:300] for c in narrative_chunks[:3]
                ])
                
                contradictions = detect_contradictions(
                    numeric_summary, narrative_summary, model_call_fn
                )
                
                # DEFENSIVE: Validate contradiction output (Area #5 - citation integrity)
                if contradictions and not isinstance(contradictions, str):
                    contradictions = str(contradictions)
                
                # DEFENSIVE: Only include if [CONTRADICTION] found
                if contradictions and "[CONTRADICTION]" not in contradictions:
                    contradictions = None
                    
            except Exception as contra_exc:
                logger.warning(f"Contradiction detection failed (non-blocking): {contra_exc}")
                contradictions = None
        
        # DEFENSIVE: Calculate metrics with fallbacks
        try:
            latency_ms = int((time.time() - start_time) * 1000)
        except Exception:
            latency_ms = 0
        
        # DEFENSIVE: Ensure all response fields are valid types
        response = QueryResponse(
            query=payload.query[:500] if payload.query else "Unknown",
            analysis=analysis[:5000] if analysis else "No analysis",
            retrieval_mode=retrieval_summary.get('query_mode', 'unknown'),
            model_used=model_used,
            numeric_data_count=max(0, retrieval_summary.get('numeric_retrieved', 0)),
            narrative_chunks_count=max(0, retrieval_summary.get('narrative_retrieved', 0)),
            sources=sources or [],
            latency_ms=latency_ms,
            tokens_used=tokens_used if isinstance(tokens_used, int) else None,
            contradictions_detected=contradictions[:500] if contradictions else None
        )
        
        logger.info(f"Query completed in {latency_ms}ms: {len(numeric_data)} metrics, {len(narrative_chunks)} narratives")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as exc:
        # DEFENSIVE: Catch all other errors, don't leak internals (Area #10)
        logger.error(f"Query processing failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Query processing failed. Please try again later."
        )
