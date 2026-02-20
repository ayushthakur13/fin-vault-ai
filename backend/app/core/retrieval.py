"""
Hybrid Retrieval Module
Combines structured PostgreSQL queries with semantic Qdrant searches
Bridges numeric financial data with narrative context
"""
from typing import Optional, TypedDict
from datetime import datetime
import json

from app.core.schema import get_financial_metrics
from app.core.vector import get_qdrant_client
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class StructuredMetrics(TypedDict, total=False):
    """Structured financial metrics retrieved from PostgreSQL"""
    company: str
    ticker: str
    year: int
    revenue: float
    net_income: float
    profit_margin_pct: float
    roe_pct: float
    roa_pct: float
    revenue_growth_pct: float
    assets: float
    equity: float
    current_ratio: float
    debt_to_equity: float


class NarrativeChunk(TypedDict):
    """Narrative text chunk retrieved from Qdrant"""
    doc_type: str
    company: str
    ticker: str
    year: int
    text: str
    section_title: str
    point_id: int
    score: float  # Similarity score from vector search


class HybridContext(TypedDict, total=False):
    """Combined context from both structured and narrative retrieval"""
    query: str
    mode: str
    numeric_data: list[StructuredMetrics]
    narrative_chunks: list[NarrativeChunk]
    retrieval_summary: dict


def retrieve_structured_metrics(
    tickers: Optional[list[str]] = None,
    companies: Optional[list[str]] = None,
    years: Optional[list[int]] = None,
    limit: int = 100
) -> list[StructuredMetrics]:
    """
    Retrieve numeric financial metrics from PostgreSQL with optional filtering.
    
    Queries structured financial data (revenue, profit margins, ratios, etc) from the
    financial_metrics table. Supports filtering by ticker, company name, or fiscal year.
    Returns most recent data by default if no year filter specified.
    
    Args:
        tickers: List of stock ticker symbols to filter (e.g., ['AAPL', 'MSFT'])
        companies: List of company names to filter (alternative to tickers)
        years: List of fiscal years to filter (e.g., [2023, 2022])
        limit: Maximum records to return per company (default 100)
        
    Returns:
        List of StructuredMetrics TypedDict records, or empty list if query fails
    """
    try:
        all_metrics = []
        
        # If specific tickers provided, query each
        if tickers:
            for ticker in tickers:
                metrics = get_financial_metrics(ticker=ticker, limit=limit)
                all_metrics.extend(metrics)
        # If companies provided
        elif companies:
            for company in companies:
                metrics = get_financial_metrics(company=company, limit=limit)
                all_metrics.extend(metrics)
        # Default: get recent metrics
        else:
            metrics = get_financial_metrics(limit=limit)
            all_metrics.extend(metrics)
        
        logger.info(f"Retrieved {len(all_metrics)} structured metric records")
        return all_metrics
        
    except Exception as exc:
        logger.error(f"Failed to retrieve structured metrics: {exc}")
        return []


def retrieve_narrative_context(
    query_embedding: list[float],
    collection_name: str = "financial_narratives",
    tickers: Optional[list[str]] = None,
    doc_types: Optional[list[str]] = None,
    limit: int = 5,
    score_threshold: float = 0.5
) -> list[NarrativeChunk]:
    """
    Retrieve narrative chunks from Qdrant using semantic search
    
    Args:
        query_embedding: Vector embedding of user query
        collection_name: Qdrant collection to search
        tickers: Filter by company ticker
        doc_types: Filter by document type
        limit: Number of results to return
        score_threshold: Minimum similarity score
        
    Returns:
        List of narrative chunks with metadata
    """
    try:
        client = get_qdrant_client()
        
        # Check if collection exists
        try:
            client.get_collection(collection_name)
        except Exception as exc:
            logger.debug(f"Qdrant collection '{collection_name}' not found: {exc}")
            return []
        
        # Build search filter if needed
        query_filter = None
        if tickers or doc_types:
            query_filter = {}
            if tickers:
                query_filter['ticker'] = {'in': tickers}
            if doc_types:
                query_filter['doc_type'] = {'in': doc_types}
        
        # Search in Qdrant
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold
        )
        
        # Convert to narrative chunks
        chunks = []
        for result in search_results:
            payload = result.payload or {}
            chunks.append(NarrativeChunk(
                doc_type=payload.get('doc_type', 'unknown'),
                company=payload.get('company', 'unknown'),
                ticker=payload.get('ticker', 'unknown'),
                year=payload.get('year', 0),
                text=payload.get('summary', ''),  # Full text stored in Qdrant payload
                section_title=payload.get('section_title', 'unknown'),
                point_id=result.id,
                score=result.score or 0.0
            ))
        
        logger.info(f"Retrieved {len(chunks)} narrative chunks from Qdrant")
        return chunks
        
    except Exception as exc:
        logger.error(f"Failed to retrieve narrative context: {exc}")
        return []


def classify_query_mode(query: str) -> str:
    """
    Classify query to determine retrieval strategy
    
    Args:
        query: User query text
        
    Returns:
        One of: 'numeric', 'narrative', 'hybrid'
    """
    query_lower = query.lower()
    
    # Numeric queries
    numeric_keywords = [
        'compare', 'revenue', 'profit', 'margin', 'roe', 'roa', 'growth',
        'vs', 'higher', 'lower', 'ratio', 'metric', 'earnings', 'assets',
        'how much', 'what is', 'financial', 'balance', 'cash', 'debt'
    ]
    
    # Narrative queries
    narrative_keywords = [
        'why', 'explain', 'management', 'risk', 'strategy', 'outlook',
        'commentary', 'discussion', 'analyst', 'transcript', 'call',
        'guidance', 'challenges', 'opportunities', 'competitive',
        'business model', 'threat', 'strength'
    ]
    
    numeric_count = sum(1 for kw in numeric_keywords if kw in query_lower)
    narrative_count = sum(1 for kw in narrative_keywords if kw in query_lower)
    
    if numeric_count > narrative_count:
        return 'numeric'
    elif narrative_count > numeric_count:
        return 'narrative'
    else:
        return 'hybrid'


def perform_hybrid_retrieval(
    query: str,
    embeddings_model_fn=None,
    tickers: Optional[list[str]] = None,
    force_mode: Optional[str] = None,
    numeric_limit: int = 50,
    narrative_limit: int = 5
) -> HybridContext:
    """
    Perform hybrid retrieval combining numeric and narrative data
    
    Args:
        query: User query
        embeddings_model_fn: Function to generate query embedding
        tickers: Filter by specific tickers
        force_mode: Override automatic mode selection ('numeric', 'narrative', 'hybrid')
        numeric_limit: Max numeric records to retrieve
        narrative_limit: Max narrative chunks to retrieve
        
    Returns:
        HybridContext with combined structured and semantic data
    """
    start_time = datetime.now()
    mode = force_mode or classify_query_mode(query)
    
    context = HybridContext(
        query=query,
        mode=mode,
        numeric_data=[],
        narrative_chunks=[],
        retrieval_summary={
            'query_mode': mode,
            'numeric_retrieved': 0,
            'narrative_retrieved': 0,
            'latency_ms': 0
        }
    )
    
    try:
        # Retrieve numeric data if needed
        if mode in ['numeric', 'hybrid']:
            numeric_data = retrieve_structured_metrics(
                tickers=tickers,
                limit=numeric_limit
            )
            context['numeric_data'] = numeric_data
            context['retrieval_summary']['numeric_retrieved'] = len(numeric_data)
        
        # Retrieve narrative data if needed and embeddings model available
        if mode in ['narrative', 'hybrid'] and embeddings_model_fn:
            try:
                query_embedding = embeddings_model_fn(query)
                narrative_chunks = retrieve_narrative_context(
                    query_embedding=query_embedding,
                    tickers=tickers,
                    limit=narrative_limit
                )
                context['narrative_chunks'] = narrative_chunks
                context['retrieval_summary']['narrative_retrieved'] = len(narrative_chunks)
            except Exception as exc:
                logger.warning(f"Failed to retrieve narrative context: {exc}")
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        context['retrieval_summary']['latency_ms'] = int(elapsed)
        
        return context
        
    except Exception as exc:
        logger.error(f"Hybrid retrieval failed: {exc}")
        return context


def format_context_for_llm(context: HybridContext) -> str:
    """
    Format hybrid context into LLM-friendly prompt section
    
    Args:
        context: HybridContext from retrieval
        
    Returns:
        Formatted context string for inclusion in LLM prompt
    """
    parts = []
    
    # Add numeric context
    if context.get('numeric_data'):
        parts.append("## FINANCIAL METRICS DATA")
        parts.append("")
        
        for metric in context['numeric_data'][:10]:  # Limit to top 10 for brevity
            parts.append(f"### {metric.get('ticker', 'Unknown')} - {metric.get('company', 'Unknown')} (FY {metric.get('year')})")
            
            metrics_to_show = [
                ('Revenue', 'revenue'),
                ('Net Income', 'net_income'),
                ('Profit Margin %', 'profit_margin_pct'),
                ('ROE %', 'roe_pct'),
                ('Revenue Growth %', 'revenue_growth_pct'),
                ('Total Assets', 'assets'),
                ('Equity', 'equity'),
            ]
            
            for label, key in metrics_to_show:
                value = metric.get(key)
                if value is not None:
                    # Convert Decimal to float for calculations
                    value_float = float(value)
                    if 'pct' in key or 'growth' in key:
                        parts.append(f"- {label}: {value_float:.2f}%")
                    elif value_float > 1000000000:
                        parts.append(f"- {label}: ${value_float/1e9:.2f}B")
                    else:
                        parts.append(f"- {label}: ${value_float/1e6:.2f}M")
            
            parts.append("")
    
    # Add narrative context
    if context.get('narrative_chunks'):
        parts.append("## NARRATIVE CONTEXT")
        parts.append("")
        
        for chunk in context['narrative_chunks'][:5]:  # Limit to top 5 for brevity
            parts.append(f"### {chunk.get('doc_type', 'Unknown').upper()} - {chunk.get('ticker')} (FY {chunk.get('year')})")
            if chunk.get('section_title'):
                parts.append(f"**{chunk['section_title']}** (Relevance: {chunk.get('score', 0):.2f})")
            parts.append(f"```\n{chunk.get('text', '')}\n```")
            parts.append("")
    
    # Add retrieval summary
    summary = context.get('retrieval_summary', {})
    parts.append("## RETRIEVAL METADATA")
    parts.append(f"- Mode: {summary.get('query_mode')}")
    parts.append(f"- Numeric Records: {summary.get('numeric_retrieved')}")
    parts.append(f"- Narrative Chunks: {summary.get('narrative_retrieved')}")
    parts.append(f"- Retrieval Latency: {summary.get('latency_ms')}ms")
    
    return "\n".join(parts)


def build_llm_prompt(
    query: str,
    context: HybridContext,
    system_role: str = "assistant"
) -> str:
    """
    Build complete LLM prompt with query and retrieved context
    
    Args:
        query: Original user query
        context: HybridContext from retrieval
        system_role: Role description for the model
        
    Returns:
        Complete prompt string
    """
    prompt_parts = [
        f"""You are a financial research agent. Your role is to {system_role}.

Analyze the following financial data and provide insights grounded in the data.
Always cite your sources and explain your reasoning.

---

USER QUERY:
{query}

---

RETRIEVED CONTEXT:
{format_context_for_llm(context)}

---

INSTRUCTIONS:
1. Answer the query using the provided financial data
2. Cite specific metrics and sources
3. If data is missing, note what additional information would help
4. Be concise but thorough
5. Highlight key insights and trends

RESPONSE:"""
    ]
    
    return "\n".join(prompt_parts)
