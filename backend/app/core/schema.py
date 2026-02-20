"""
PostgreSQL schema initialization for FinVault AI
Defines tables for structured financial data ingestion
"""
import psycopg2
from psycopg2.extras import execute_values
from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


SCHEMA_DDL = """

-- Financial metrics table (numeric, deterministic data from SEC filings)
CREATE TABLE IF NOT EXISTS financial_metrics (
    id SERIAL PRIMARY KEY,
    company VARCHAR(50) NOT NULL,
    ticker VARCHAR(10),
    cik INTEGER,
    year INTEGER NOT NULL,
    
    -- Base metrics from SEC XBRL (in USD)
    revenue NUMERIC,
    net_income NUMERIC,
    gross_profit NUMERIC,
    operating_income NUMERIC,
    operating_cashflow NUMERIC,
    capex NUMERIC,
    free_cashflow NUMERIC,
    
    -- Balance sheet metrics
    assets NUMERIC,
    current_assets NUMERIC,
    liabilities NUMERIC,
    current_liabilities NUMERIC,
    equity NUMERIC,
    long_term_debt NUMERIC,
    cash NUMERIC,
    
    -- Calculated ratios (percentage/decimal)
    profit_margin_pct NUMERIC,
    gross_margin_pct NUMERIC,
    roe_pct NUMERIC,
    roa_pct NUMERIC,
    current_ratio NUMERIC,
    debt_to_equity NUMERIC,
    
    -- Growth rates (YoY %)
    revenue_growth_pct NUMERIC,
    net_income_growth_pct NUMERIC,
    assets_growth_pct NUMERIC,
    
    -- Source and timing
    source_file VARCHAR(255),
    data_source VARCHAR(50) DEFAULT 'SEC_EDGAR',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fiscal_year_end DATE,
    
    -- For tracking updates
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(company, year)
);

-- Create indexes for financial_metrics
CREATE INDEX IF NOT EXISTS idx_company_year ON financial_metrics (company, year);
CREATE INDEX IF NOT EXISTS idx_ticker_year ON financial_metrics (ticker, year);

-- Narrative text chunks for semantic search (via Qdrant)
-- This table stores metadata about embedded documents
CREATE TABLE IF NOT EXISTS narrative_documents (
    id SERIAL PRIMARY KEY,
    company VARCHAR(50) NOT NULL,
    ticker VARCHAR(10),
    year INTEGER,
    
    -- Document classification
    doc_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(500),
    source_file VARCHAR(255),
    
    -- Reference to Qdrant collection and vector ID
    qdrant_collection VARCHAR(100),
    qdrant_point_id BIGINT,
    
    -- Metadata for retrieval
    chunk_id INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    section_title VARCHAR(255),
    
    -- Content summary for quick lookup
    summary TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(qdrant_point_id, qdrant_collection)
);

-- Create indexes for narrative_documents
CREATE INDEX IF NOT EXISTS idx_company_doc_type ON narrative_documents (company, doc_type);
CREATE INDEX IF NOT EXISTS idx_qdrant_id ON narrative_documents (qdrant_point_id);

-- User financial preferences and watchlists
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Favorite companies/tickers
    watchlist TEXT,
    preferred_metrics TEXT,
    
    -- Analysis preferences
    default_mode VARCHAR(20) DEFAULT 'quick',
    max_context_tokens INTEGER DEFAULT 8000,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query history and traceability
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    query TEXT NOT NULL,
    mode VARCHAR(20),
    
    -- Retrieval metadata
    retrieved_metrics_count INTEGER DEFAULT 0,
    retrieved_narrative_count INTEGER DEFAULT 0,
    
    -- Response metadata
    response TEXT,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    latency_ms INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for query_history
CREATE INDEX IF NOT EXISTS idx_user_created ON query_history (user_id, created_at);

"""


def init_schema():
    """Initialize PostgreSQL schema if needed"""
    try:
        with psycopg2.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_DDL)
                conn.commit()
        logger.info("PostgreSQL schema initialized successfully")
        return True
    except Exception as exc:
        logger.error("Failed to initialize schema: %s", exc)
        return False


def insert_financial_metrics(data: list[dict]) -> int:
    """
    Batch insert financial metrics into PostgreSQL
    
    Args:
        data: List of financial metric dicts
        
    Returns:
        Number of rows inserted
    """
    if not data:
        return 0
    
    try:
        with psycopg2.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                # Extract column names from first record
                columns = list(data[0].keys())
                placeholders = ','.join(['%s'] * len(columns))
                column_names = ','.join(columns)
                
                query = f"""
                    INSERT INTO financial_metrics ({column_names})
                    VALUES ({placeholders})
                    ON CONFLICT (company, year) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    {', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in ['company', 'year']])}
                """
                
                # Batch insert all records at once for performance
                values_list = [tuple(record.get(col) for col in columns) for record in data]
                rows_inserted = execute_values(cur, query, values_list, page_size=1000)
                conn.commit()
        
        logger.info("Inserted %d financial metric records", rows_inserted)
        return rows_inserted
        
    except Exception as exc:
        logger.error("Failed to insert financial metrics: %s", exc)
        return 0


def get_financial_metrics(
    company: str = None,
    ticker: str = None,
    year: int = None,
    limit: int = 100
) -> list[dict]:
    """
    Retrieve financial metrics from PostgreSQL
    
    Args:
        company: Company name filter
        ticker: Ticker filter
        year: Fiscal year filter
        limit: Result limit
        
    Returns:
        List of metric records as dicts
    """
    try:
        with psycopg2.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM financial_metrics WHERE 1=1"
                params = []
                
                if company:
                    query += " AND company = %s"
                    params.append(company)
                if ticker:
                    query += " AND ticker = %s"
                    params.append(ticker)
                if year:
                    query += " AND year = %s"
                    params.append(year)
                
                query += " ORDER BY year DESC LIMIT %s"
                params.append(limit)
                cur.execute(query, params)
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
                
    except Exception as exc:
        logger.error("Failed to retrieve financial metrics: %s", exc)
        return []


def register_narrative_document(
    company: str,
    ticker: str,
    year: int,
    doc_type: str,
    qdrant_point_id: int,
    qdrant_collection: str,
    chunk_id: int = 0,
    total_chunks: int = 1,
    section_title: str = None,
    summary: str = None,
    source_file: str = None,
    source_url: str = None
) -> int:
    """
    Register a narrative document embedding in Qdrant with metadata in PostgreSQL
    
    Returns:
        Inserted row ID
    """
    try:
        with psycopg2.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO narrative_documents 
                    (company, ticker, year, doc_type, qdrant_point_id, qdrant_collection,
                     chunk_id, total_chunks, section_title, summary, source_file, source_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                cur.execute(query, (
                    company, ticker, year, doc_type, qdrant_point_id, qdrant_collection,
                    chunk_id, total_chunks, section_title, summary, source_file, source_url
                ))
                row_id = cur.fetchone()[0]
                conn.commit()
        
        return row_id
        
    except Exception as exc:
        logger.error("Failed to register narrative document: %s", exc)
        return 0
