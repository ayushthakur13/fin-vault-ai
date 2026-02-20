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
    
    DEFENSIVE: Gracefully handles database failures, missing data, and malformed records.
    - Empty tickers → returns empty list
    - Database connection failure → returns empty list
    - Malformed rows → skips them and continues
    - NULL metric values → allowed (None), not filtered
    - Invalid years → filters out non-int or out-of-range values
    
    Queries structured financial data (revenue, profit margins, ratios, etc) from the
    financial_metrics table. Supports filtering by ticker, company name, or fiscal year.
    Returns most recent data by default if no year filter specified.
    
    Args:
        tickers: List of stock ticker symbols to filter (e.g., ['AAPL', 'MSFT'])
        companies: List of company names to filter (alternative to tickers)
        years: List of fiscal years to filter (e.g., [2023, 2022])
        limit: Maximum records to return per company (default 100, capped at 100)
        
    Returns:
        List of StructuredMetrics TypedDict records, or empty list if query fails
    """
    # DEFENSIVE: Sanitize inputs
    limit = min(max(limit, 1), 100)
    
    # DEFENSIVE: Normalize tickers to uppercase, filter empty strings
    if tickers:
        tickers = [t.upper().strip() for t in tickers if isinstance(t, str) and t.strip()]
        if not tickers:  # If all tickers were empty strings
            logger.debug("All tickers filtered out as empty strings")
            return []
    
    # DEFENSIVE: Normalize companies, filter empty strings
    if companies:
        companies = [c.strip() for c in companies if isinstance(c, str) and c.strip()]
        if not companies:  # If all companies were empty strings
            logger.debug("All companies filtered out as empty strings")
            return []
    
    # DEFENSIVE: Filter years to reasonable range
    if years:
        years = [y for y in years if isinstance(y, int) and 2000 <= y <= 2100]
        if not years:
            logger.debug("All years filtered out as invalid")
            years = None  # Fall through to default query
    
    try:
        all_metrics = []
        
        # If specific tickers provided, query each
        if tickers:
            for ticker in tickers:
                try:
                    metrics = get_financial_metrics(ticker=ticker, limit=limit)
                    
                    # DEFENSIVE: Ensure metrics is list
                    if not isinstance(metrics, list):
                        logger.warning(f"Non-list result for ticker {ticker}: {type(metrics)}")
                        continue
                    
                    # DEFENSIVE: Validate and filter each record
                    valid_metrics = []
                    for metric in metrics:
                        if not isinstance(metric, dict):
                            logger.warning(f"Non-dict metric in results: {type(metric)}")
                            continue
                        
                        # DEFENSIVE: Ensure required fields
                        if not metric.get('ticker') or not metric.get('company'):
                            logger.warning(f"Skipping metric missing ticker/company: {metric}")
                            continue
                        
                        # DEFENSIVE: Validate year if present
                        year = metric.get('year')
                        if year is not None and (not isinstance(year, int) or year < 2000 or year > 2100):
                            logger.warning(f"Skipping metric with invalid year {year}: {metric}")
                            continue
                        
                        valid_metrics.append(metric)
                    
                    all_metrics.extend(valid_metrics)
                    logger.debug(f"Retrieved {len(valid_metrics)} metrics for ticker {ticker}")
                    
                except Exception as ticker_exc:
                    logger.warning(f"Failed to retrieve metrics for ticker {ticker}: {ticker_exc}")
                    continue
        
        # If companies provided (but no tickers)
        elif companies:
            for company in companies:
                try:
                    metrics = get_financial_metrics(company=company, limit=limit)
                    
                    if not isinstance(metrics, list):
                        logger.warning(f"Non-list result for company {company}: {type(metrics)}")
                        continue
                    
                    valid_metrics = []
                    for metric in metrics:
                        if not isinstance(metric, dict):
                            logger.warning(f"Non-dict metric in results: {type(metric)}")
                            continue
                        if not metric.get('company'):
                            logger.warning(f"Skipping metric missing company: {metric}")
                            continue
                        
                        year = metric.get('year')
                        if year is not None and (not isinstance(year, int) or year < 2000 or year > 2100):
                            logger.warning(f"Skipping metric with invalid year {year}: {metric}")
                            continue
                        
                        valid_metrics.append(metric)
                    
                    all_metrics.extend(valid_metrics)
                    logger.debug(f"Retrieved {len(valid_metrics)} metrics for company {company}")
                    
                except Exception as company_exc:
                    logger.warning(f"Failed to retrieve metrics for company {company}: {company_exc}")
                    continue
        
        # Default: get recent metrics
        else:
            try:
                metrics = get_financial_metrics(limit=limit)
                
                if not isinstance(metrics, list):
                    logger.warning(f"Non-list result for default query: {type(metrics)}")
                    return []
                
                valid_metrics = []
                for metric in metrics:
                    if not isinstance(metric, dict):
                        logger.warning(f"Non-dict metric in results: {type(metric)}")
                        continue
                    
                    year = metric.get('year')
                    if year is not None and (not isinstance(year, int) or year < 2000 or year > 2100):
                        logger.warning(f"Skipping metric with invalid year {year}: {metric}")
                        continue
                    
                    valid_metrics.append(metric)
                
                all_metrics.extend(valid_metrics)
                logger.debug(f"Retrieved {len(valid_metrics)} default metrics")
                
            except Exception as default_exc:
                logger.warning(f"Failed to retrieve default metrics: {default_exc}")
        
        logger.info(f"Retrieved {len(all_metrics)} total structured metric records")
        return all_metrics
        
    except Exception as exc:
        logger.error(f"Critical error in retrieve_structured_metrics: {exc}")
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
    Classify query to determine retrieval strategy deterministically.
    
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
    
    # DEFENSIVE: Log classification for debugging
    logger.debug(f"Query classification: numeric_kw={numeric_count}, narrative_kw={narrative_count}")
    
    if numeric_count > narrative_count:
        mode = 'numeric'
    elif narrative_count > numeric_count:
        mode = 'narrative'
    else:
        mode = 'hybrid'
    
    logger.debug(f"Query mode determined: {mode}")
    return mode


def perform_hybrid_retrieval(
    query: str,
    embeddings_model_fn=None,
    tickers: Optional[list[str]] = None,
    force_mode: Optional[str] = None,
    numeric_limit: int = 50,
    narrative_limit: int = 5
) -> HybridContext:
    """
    Perform hybrid retrieval combining numeric and narrative data.
    
    Intelligently routes queries to numeric-only, narrative-only, or hybrid retrieval
    based on keywords. For hybrid queries, retrieves both structured financial metrics
    and narrative excerpts from earnings calls/filings, then assembles them into a
    citation-rich context for LLM reasoning.
    
    Gracefully handles missing data (Qdrant down, no narratives) without blocking.
    
    Args:
        query: User query
        embeddings_model_fn: Function to generate query embedding
        tickers: Filter by specific tickers
        force_mode: Override automatic mode selection ('numeric', 'narrative', 'hybrid')
        numeric_limit: Max numeric records to retrieve (capped at 100)
        narrative_limit: Max narrative chunks to retrieve (capped at 5)
        
    Returns:
        HybridContext with combined structured and semantic data, or empty if all retrieval fails
    """
    from app.core.vector import search_narrative
    
    # DEFENSIVE: Sanitize limits
    numeric_limit = min(max(numeric_limit, 10), 100)
    narrative_limit = min(max(narrative_limit, 1), 5)
    
    start_time = datetime.now()
    mode = force_mode or classify_query_mode(query)
    logger.info(f"Performing {mode} retrieval for query: {query[:80]}")
    
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
            try:
                numeric_data = retrieve_structured_metrics(
                    tickers=tickers,
                    limit=numeric_limit
                )
                # DEFENSIVE: Ensure numeric_data is list
                if numeric_data is None:
                    numeric_data = []
                context['numeric_data'] = numeric_data
                context['retrieval_summary']['numeric_retrieved'] = len(numeric_data)
                logger.info(f"Retrieved {len(numeric_data)} numeric records")
            except Exception as exc:
                logger.warning(f"Numeric retrieval failed: {exc}")
                context['numeric_data'] = []
        
        # Retrieve narrative data if needed and embeddings model available
        if mode in ['narrative', 'hybrid'] and embeddings_model_fn:
            try:
                query_embedding = embeddings_model_fn(query)
                
                # DEFENSIVE: Validate embedding
                if not query_embedding or len(query_embedding) == 0:
                    logger.warning("Query embedding is empty")
                else:
                    # Use search_narrative with safe defaults
                    narrative_results = search_narrative(
                        query_embedding=query_embedding,
                        tickers=tickers,
                        top_k=narrative_limit,
                        score_threshold=0.4
                    )
                    
                    # DEFENSIVE: Ensure results is list
                    if narrative_results is None:
                        narrative_results = []
                    
                    # Convert to NarrativeChunk format
                    narrative_chunks = []
                    for result in narrative_results[:narrative_limit]:  # Double-check limit
                        try:
                            metadata = result.get('metadata', {})
                            narrative_chunks.append(NarrativeChunk(
                                doc_type=metadata.get('doc_type', 'unknown'),
                                company=metadata.get('company', 'Unknown'),
                                ticker=metadata.get('ticker', 'Unknown'),
                                year=metadata.get('year', 0),
                                text=result.get('text', '')[:800],  # Cap text
                                section_title=metadata.get('section_title', ''),
                                point_id=result.get('point_id', 0),
                                score=max(0.0, min(result.get('similarity_score', 0.0), 1.0))  # Clamp score
                            ))
                        except Exception as chunk_exc:
                            logger.warning(f"Failed to parse narrative chunk: {chunk_exc}")
                            continue
                    
                    context['narrative_chunks'] = narrative_chunks
                    context['retrieval_summary']['narrative_retrieved'] = len(narrative_chunks)
                    logger.info(f"Retrieved {len(narrative_chunks)} narrative chunks")
                    
            except Exception as exc:
                logger.warning(f"Narrative retrieval failed (non-blocking): {exc}")
                context['narrative_chunks'] = []
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        context['retrieval_summary']['latency_ms'] = int(elapsed)
        logger.debug(f"Retrieval completed in {elapsed:.0f}ms: {len(context['numeric_data'])} metrics, {len(context['narrative_chunks'])} narratives")
        
        return context
        
    except Exception as exc:
        logger.error(f"Hybrid retrieval critical error: {exc}")
        # Return partial context even on error
        context['retrieval_summary']['latency_ms'] = int((datetime.now() - start_time).total_seconds() * 1000)
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


def assemble_context(
    query: str,
    numeric_data: list[dict],
    narrative_chunks: list[dict],
    include_contradiction_check: bool = True
) -> str:
    """
    Assemble retrieved data into structured, citation-rich context for LLM.
    
    DEFENSIVE: Gracefully handles malformed/missing data.
    - Caps narrative chunks at 5 max (Area #4 safeguard)
    - Validates text length (800 char per chunk, 5000 char total narrative)
    - Ensures every narrative item has [Source: ...] label
    - Caps numeric metrics at 15
    - Skips malformed records, logs warnings
    
    Formats numeric metrics and narrative excerpts with source labels, creating
    a human-readable prompt context that enables the model to cite sources and
    identify potential contradictions between quantitative and qualitative data.
    
    Args:
        query: Original user query
        numeric_data: List of financial metric records from PostgreSQL
        narrative_chunks: List of narrative chunk records from Qdrant with metadata
        include_contradiction_check: Add prompt instruction to detect contradictions
        
    Returns:
        Formatted context string optimized for LLM reasoning with citations
    """
    sections = []
    
    # DEFENSIVE: Validate inputs
    if not isinstance(query, str):
        query = str(query or "")
    if not isinstance(numeric_data, list):
        numeric_data = []
    if not isinstance(narrative_chunks, list):
        narrative_chunks = []
    
    # Query context
    sections.append("=" * 70)
    sections.append("FINANCIAL RESEARCH CONTEXT")
    sections.append("=" * 70)
    sections.append(f"\nQuery: {query}\n")
    
    # Numeric metrics section
    if numeric_data:
        sections.append("\n💾 FINANCIAL METRICS DATA")
        sections.append("-" * 70)
        
        # DEFENSIVE: Cap at 15 metrics, validate each record
        for metric in numeric_data[:15]:
            if not isinstance(metric, dict):
                logger.warning(f"Skipping non-dict metric: {type(metric)}")
                continue
            
            try:
                ticker = metric.get('ticker', 'Unknown')
                company = metric.get('company', 'Unknown')
                year = metric.get('year', 'N/A')
                
                # DEFENSIVE: Ensure ticker/company not empty
                if not ticker or not company:
                    logger.warning(f"Skipping metric missing ticker/company")
                    continue
                
                sections.append(f"\n📊 {company} ({ticker}) - FY {year}")
                sections.append("   Metrics:")
                
                # Key metrics to display
                metric_items = [
                    ('Revenue', 'revenue', 'B'),
                    ('Net Income', 'net_income', 'B'),
                    ('Profit Margin', 'profit_margin_pct', '%'),
                    ('ROE', 'roe_pct', '%'),
                    ('Revenue Growth', 'revenue_growth_pct', '%'),
                    ('Total Assets', 'assets', 'B'),
                ]
                
                for label, key, unit in metric_items:
                    value = metric.get(key)
                    if value is not None:
                        try:
                            value_float = float(value)
                            if unit == '%':
                                sections.append(f"   • {label}: {value_float:.2f}%")
                            elif unit == 'B':
                                if value_float > 1e9:
                                    sections.append(f"   • {label}: ${value_float/1e9:.2f}B")
                                else:
                                    sections.append(f"   • {label}: ${value_float/1e6:.2f}M")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert {key}={value} to float")
                            continue
            except Exception as metric_exc:
                logger.warning(f"Error processing metric: {metric_exc}")
                continue
    
    # Narrative section
    if narrative_chunks:
        sections.append("\n\n📝 EARNINGS COMMENTARY & NARRATIVE CONTEXT")
        sections.append("-" * 70)
        
        # DEFENSIVE: Cap at 5 narrative chunks (Area #4 safeguard)
        capped_chunks = narrative_chunks[:5]
        if len(narrative_chunks) > 5:
            logger.debug(f"Narrative chunks capped at 5 (had {len(narrative_chunks)})")
        
        total_narrative_length = 0
        narrative_count = 0
        
        # Group by document type and source for better organization
        by_source = {}
        for chunk in capped_chunks:
            if not isinstance(chunk, dict):
                logger.warning(f"Skipping non-dict narrative chunk: {type(chunk)}")
                continue
            
            metadata = chunk.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            
            ticker = metadata.get('ticker', 'Unknown')
            doc_type = metadata.get('doc_type', 'unknown')
            section = metadata.get('section_title', 'Full Document')
            year = metadata.get('year', 'N/A')
            
            # DEFENSIVE: Ensure source label is not empty
            if not ticker or ticker == 'Unknown':
                logger.warning(f"Skipping narrative chunk with missing ticker")
                continue
            
            source_key = f"{ticker} {doc_type.replace('_', ' ').title()} FY{year}"
            if source_key not in by_source:
                by_source[source_key] = []
            by_source[source_key].append((section, chunk))
        
        for source_label, chunks_list in by_source.items():
            for section_title, chunk in chunks_list:
                # DEFENSIVE: Cap total narrative length (5000 chars max)
                if total_narrative_length > 5000:
                    logger.debug(f"Narrative context exceeded 5000 char limit, truncating")
                    break
                
                try:
                    # DEFENSIVE: Ensure source label is present (Area #5 safeguard)
                    source_label_safe = source_label.replace('<', '').replace('>', '')  # Sanitize
                    sections.append(f"\n[Source: {source_label_safe}]")
                    
                    if section_title and section_title != source_label:
                        section_title_safe = str(section_title)[:100]  # Cap at 100 chars
                        sections.append(f"Section: {section_title_safe}")
                    
                    # Format narrative text with proper indentation
                    text = chunk.get('text', '')
                    if not isinstance(text, str):
                        text = str(text or "")
                    
                    similarity = chunk.get('similarity_score', 0)
                    try:
                        similarity = float(similarity)
                        similarity = max(0.0, min(similarity, 1.0))  # Clamp 0-1
                    except (ValueError, TypeError):
                        similarity = 0.0
                    
                    sections.append(f"Relevance Score: {similarity:.3f}")
                    
                    # DEFENSIVE: Cap individual chunk text at 800 chars (Area #4 safeguard)
                    text_capped = text[:800]
                    sections.append("\n" + "```")
                    sections.append(text_capped)
                    if len(text) > 800:
                        sections.append("...[truncated]")
                    sections.append("```\n")
                    
                    total_narrative_length += len(text_capped)
                    narrative_count += 1
                    
                except Exception as chunk_exc:
                    logger.warning(f"Error processing narrative chunk: {chunk_exc}")
                    continue
    
    # Instructions section
    sections.append("\n" + "=" * 70)
    sections.append("ANALYSIS INSTRUCTIONS")
    sections.append("=" * 70)
    sections.append("""
You are a financial research agent. Analyze the provided data and respond to the query.

REQUIREMENTS:
1. Ground all claims in the provided metrics or citations
2. Use [Source: ...] labels to cite where each insight originates
3. Compare numeric data with narrative insights where relevant
4. Identify any contradictions between quantitative metrics and qualitative commentary
5. Provide both bull and bear perspectives when appropriate
6. Quantify risks and opportunities with specific metrics
7. Flag any data inconsistencies or missing information

FORMATTING:
- Use bullet points for key findings
- Bold important figures and quotes
- Structure analysis: Summary → Key Metrics → Narrative Insights → Risks → Conclusions
    """)
    
    if include_contradiction_check:
        sections.append("""\nCONTRADICTION DETECTION:
If any earnings commentary contradicts the financial metrics (e.g., management
claims "strong growth" but metrics show declining revenue), highlight this explicitly.
Example: "[ALERT] Management stated 'record Q4 performance' but YoY revenue declined 3%"
    """)
    
    return "\n".join(sections)
    
    # Instructions section
    sections.append("\n" + "=" * 70)
    sections.append("ANALYSIS INSTRUCTIONS")
    sections.append("=" * 70)
    sections.append("""
You are a financial research agent. Analyze the provided data and respond to the query.

REQUIREMENTS:
1. Ground all claims in the provided metrics or citations
2. Use [Source: ...] labels to cite where each insight originates
3. Compare numeric data with narrative insights where relevant
4. Identify any contradictions between quantitative metrics and qualitative commentary
5. Provide both bull and bear perspectives when appropriate
6. Quantify risks and opportunities with specific metrics
7. Flag any data inconsistencies or missing information

FORMATTING:
- Use bullet points for key findings
- Bold important figures and quotes
- Structure analysis: Summary → Key Metrics → Narrative Insights → Risks → Conclusions
    """)
    
    if include_contradiction_check:
        sections.append("""\nCONTRADICTION DETECTION:
If any earnings commentary contradicts the financial metrics (e.g., management
claims "strong growth" but metrics show declining revenue), highlight this explicitly.
Example: "[ALERT] Management stated 'record Q4 performance' but YoY revenue declined 3%"
    """)
    
    return "\n".join(sections)


def detect_contradictions(
    numeric_summary: str,
    narrative_summary: str,
    llm_call_fn
) -> Optional[str]:
    """
    Use LLM to detect contradictions between metrics and narrative.
    
    DEFENSIVE: Wraps LLM errors gracefully (Area #6 safeguard).
    - Catches LLM timeouts and call failures
    - Validates output format (ALIGNED | CONTRADICTION | UNCLEAR)
    - Returns None on error (non-blocking)
    - Ensures no stack traces leak to user
    
    Sends both quantitative and qualitative data to the model with a specific
    prompt to identify inconsistencies. Simple prompt-based approach (no separate
    classifier required).
    
    Args:
        numeric_summary: Formatted summary of financial metrics
        narrative_summary: Formatted summary of narrative excerpts
        llm_call_fn: Function to call LLM (e.g., quick_model_call)
        
    Returns:
        String with detected contradictions, or None if none found or error occurs
    """
    # DEFENSIVE: Validate inputs
    if not isinstance(numeric_summary, str):
        numeric_summary = str(numeric_summary or "")
    if not isinstance(narrative_summary, str):
        narrative_summary = str(narrative_summary or "")
    
    if not numeric_summary and not narrative_summary:
        logger.debug("Skipping contradiction detection: both summaries empty")
        return None
    
    prompt = f"""You are a financial auditor. Review the following financial metrics and 
narrative excerpts for contradictions.

FINANCIAL METRICS:
{numeric_summary[:2000]}

NARRATIVE (from earnings calls and filings):
{narrative_summary[:2000]}

Identify ANY statements in the narrative that contradict the metrics. Examples:
- Claims of growth when metrics show decline
- Confidence in outlook when metrics deteriorated
- Company denying risks that metrics show
- Quantitative guidance inconsistent with historical trends

CRITICAL: Your response MUST start with one of these three keywords:
[CONTRADICTION] - if you found contradictions
[ALIGNED] - if metrics and narrative are consistent
[UNCLEAR] - if insufficient data to determine

Format output:
[CONTRADICTION] if found: <specific contradiction with evidence>
[ALIGNED] if consistent
[UNCLEAR] if insufficient data
"""
    
    try:
        # DEFENSIVE: Catch LLM call errors
        try:
            result = llm_call_fn(prompt)
        except Exception as llm_exc:
            logger.warning(f"LLM call failed for contradiction detection: {llm_exc}")
            return None
        
        if not result:
            logger.warning("LLM returned empty result for contradiction detection")
            return None
        
        # DEFENSIVE: Extract output field safely
        if isinstance(result, dict):
            output = result.get("output", "")
        else:
            output = str(result)
        
        if not isinstance(output, str):
            output = str(output or "")
        
        output = output.strip()[:500]  # Cap at 500 chars
        
        # DEFENSIVE: Validate output classification (Area #6 safeguard)
        valid_classifications = ["[CONTRADICTION]", "[ALIGNED]", "[UNCLEAR]"]
        has_valid_classification = any(cls in output for cls in valid_classifications)
        
        if not has_valid_classification:
            logger.warning(f"LLM output missing valid classification. Output: {output[:100]}")
            return "[UNCLEAR]: Output format error"
        
        logger.debug(f"Contradiction detection result: {output[:80]}")
        return output
        
    except Exception as exc:
        # DEFENSIVE: Catch all errors, prevent stack trace leakage (Area #10)
        logger.error(f"Contradiction detection critical error: {exc}")
        return None
