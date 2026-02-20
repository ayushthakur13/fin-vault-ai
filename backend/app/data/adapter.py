"""
Data Adapter Module
Converts raw pipeline outputs (CSVs) into structured data for AI agent
Bridges SEC EDGAR pipeline → PostgreSQL (numeric) + Qdrant (narrative)
"""
import os
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
from uuid import uuid4

from app.config import DATA_OUTPUT_DIR, settings
from app.core.schema import insert_financial_metrics, register_narrative_document
from app.core.vector import get_qdrant_client
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def load_annual_csv_to_metrics(csv_path: str, ticker: str, company: str, cik: int) -> list[dict]:
    """
    Load company annual CSV from bulk_download pipeline and convert to financial metrics.
    
    Converts SEC XBRL-derived CSV data (from bulk_download output) into standardized
    financial metric records. Handles metric extraction, type conversion, and validation.
    
    CSV columns expected: fiscal year (fy), financial metrics (Revenue, Assets, etc),
    calculated ratios (ROE, debt_to_equity, etc), and growth rates (YoY percentages).
    
    Args:
        csv_path: Path to {TICKER}_annual.csv from bulk_download directory
        ticker: Stock ticker symbol (e.g., 'AAPL')
        company: Full company name
        cik: SEC Central Index Key identifier
        
    Returns:
        List of metric record dicts with validated values ready for PostgreSQL insertion
    """
    try:
        df = pd.read_csv(csv_path)
        
        records = []
        for _, row in df.iterrows():
            # Extract metric columns (skip date/form/period columns)
            record = {
                'company': company,
                'ticker': ticker,
                'cik': cik,
                'year': int(row.get('fy')) if pd.notna(row.get('fy')) else None,
                
                # Base metrics (convert from scientific notation to plain floats)
                'revenue': float(row.get('Revenue')) if pd.notna(row.get('Revenue')) else None,
                'net_income': float(row.get('NetIncome')) if pd.notna(row.get('NetIncome')) else None,
                'gross_profit': float(row.get('GrossProfit')) if pd.notna(row.get('GrossProfit')) else None,
                'operating_income': float(row.get('OperatingIncome')) if pd.notna(row.get('OperatingIncome')) else None,
                'operating_cashflow': float(row.get('OperatingCashFlow')) if pd.notna(row.get('OperatingCashFlow')) else None,
                'capex': float(row.get('Capex')) if pd.notna(row.get('Capex')) else None,
                'free_cashflow': float(row.get('CalculatedFCF')) if pd.notna(row.get('CalculatedFCF')) else None,
                
                # Balance sheet
                'assets': float(row.get('Assets')) if pd.notna(row.get('Assets')) else None,
                'current_assets': float(row.get('CurrentAssets')) if pd.notna(row.get('CurrentAssets')) else None,
                'liabilities': float(row.get('Liabilities')) if pd.notna(row.get('Liabilities')) else None,
                'current_liabilities': float(row.get('CurrentLiabilities')) if pd.notna(row.get('CurrentLiabilities')) else None,
                'equity': float(row.get('Equity')) if pd.notna(row.get('Equity')) else None,
                'long_term_debt': float(row.get('LongTermDebt')) if pd.notna(row.get('LongTermDebt')) else None,
                'cash': float(row.get('Cash')) if pd.notna(row.get('Cash')) else None,
                
                # Calculated ratios (already in %)
                'profit_margin_pct': float(row.get('ProfitMargin')) if pd.notna(row.get('ProfitMargin')) else None,
                'gross_margin_pct': float(row.get('GrossMargin')) if pd.notna(row.get('GrossMargin')) else None,
                'roe_pct': float(row.get('ROE')) if pd.notna(row.get('ROE')) else None,
                'roa_pct': float(row.get('ROA')) if pd.notna(row.get('ROA')) else None,
                'current_ratio': float(row.get('CurrentRatio')) if pd.notna(row.get('CurrentRatio')) else None,
                'debt_to_equity': float(row.get('DebtToEquity')) if pd.notna(row.get('DebtToEquity')) else None,
                
                # Growth rates (already in %)
                'revenue_growth_pct': float(row.get('Revenue_YoY_%')) if pd.notna(row.get('Revenue_YoY_%')) else None,
                'net_income_growth_pct': float(row.get('NetIncome_YoY_%')) if pd.notna(row.get('NetIncome_YoY_%')) else None,
                'assets_growth_pct': float(row.get('Assets_YoY_%')) if pd.notna(row.get('Assets_YoY_%')) else None,
                
                # Source
                'source_file': os.path.basename(csv_path),
                'fiscal_year_end': pd.to_datetime(row.get('end')) if pd.notna(row.get('end')) else None,
            }
            
            # Only add record if it has a valid year
            if record['year'] is not None:
                records.append(record)
        
        logger.info(f"Loaded {len(records)} metric records from {csv_path}")
        return records
        
    except Exception as exc:
        logger.error(f"Failed to load CSV {csv_path}: {exc}")
        return []


def ingest_bulk_download_data(
    bulk_download_dir: Optional[str] = None,
    tickers: Optional[list] = None
) -> dict:
    """
    Ingest all annual CSV files from bulk_download directory into PostgreSQL
    
    Args:
        bulk_download_dir: Override default bulk_download directory path
        tickers: Filter to specific tickers (e.g., ['AAPL', 'MSFT'])
        
    Returns:
        Summary dict with ingestion stats
    """
    bulk_dir = Path(bulk_download_dir or DATA_OUTPUT_DIR / 'bulk_download')
    
    if not bulk_dir.exists():
        logger.error(f"Bulk download directory not found: {bulk_dir}")
        return {'success': False, 'error': 'Directory not found', 'companies': {}}
    
    summary = {'success': True, 'companies': {}}
    
    # Load summary CSV to get company metadata
    summary_csv = list(bulk_dir.glob('summary_*.csv'))
    if not summary_csv:
        logger.warning("No summary CSV found for company metadata")
        company_metadata = {}
    else:
        summary_df = pd.read_csv(summary_csv[0])
        company_metadata = {
            row['Ticker']: {
                'company': row['Company'],
                'cik': row['CIK']
            }
            for _, row in summary_df.iterrows()
        }
    
    # Find and ingest all annual CSVs
    for csv_file in sorted(bulk_dir.glob('*_annual.csv')):
        ticker = csv_file.stem.split('_')[0]
        
        # Skip if not in filter list
        if tickers and ticker not in tickers:
            continue
        
        metadata = company_metadata.get(ticker, {})
        company = metadata.get('company', ticker)
        cik = metadata.get('cik', 0)
        
        # Load and convert CSV
        records = load_annual_csv_to_metrics(str(csv_file), ticker, company, cik)
        
        # Insert into PostgreSQL
        if records:
            inserted = insert_financial_metrics(records)
            summary['companies'][ticker] = {
                'file': csv_file.name,
                'records_loaded': len(records),
                'records_inserted': inserted,
                'success': inserted > 0
            }
            logger.info(f"Ingested {inserted} records for {ticker}")
        else:
            summary['companies'][ticker] = {
                'file': csv_file.name,
                'records_loaded': 0,
                'records_inserted': 0,
                'success': False
            }
    
    return summary


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split narrative text into overlapping chunks for embedding and vector storage.
    
    Creates semantic chunks suitable for embedding models (e.g., sentence-transformers).
    Overlapping chunks improve retrieval quality by preserving context at chunk boundaries.
    Uses word-based tokenization (approximate); for precise token counting use tiktoken.
    
    Args:
        text: Full narrative text to chunk (e.g., 10-K filing, earnings call transcript)
        chunk_size: Target words per chunk (default 500 ~= 1500 tokens for business text)
        overlap: Word overlap between consecutive chunks (default 100 ~= 300 tokens)
        
    Returns:
        List of overlapping text chunks, or empty list if text too short (<50 chars)
    """
    if not text or len(text.strip()) < 50:
        return []
    
    # Simple tokenization by splitting on sentences/words
    # For production, use tiktoken or similar
    words = text.split()
    chunks = []
    i = 0
    
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk = ' '.join(words[i:end])
        chunks.append(chunk)
        
        # Move forward with overlap
        i = end - overlap if end - overlap > i else end
        
        if i >= len(words):
            break
    
    return chunks





def create_qdrant_collection_if_needed(collection_name: str = "financial_narratives") -> bool:
    """
    Create Qdrant collection for narrative embeddings if it doesn't exist
    
    Args:
        collection_name: Name of collection to create
        
    Returns:
        True if successful or already exists
    """
    try:
        client = get_qdrant_client()
        
        # Check if collection exists
        try:
            client.get_collection(collection_name)
            logger.info(f"Qdrant collection '{collection_name}' already exists")
            return True
        except Exception:
            pass
        
        # Create collection with vector size 384 (for BGE-small embeddings)
        from qdrant_client.models import Distance, VectorParams
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        
        logger.info(f"Created Qdrant collection: {collection_name}")
        return True
        
    except Exception as exc:
        logger.error(f"Failed to create Qdrant collection: {exc}")
        return False


def embed_and_store_narrative(
    text: str,
    collection_name: str,
    company: str,
    ticker: str,
    year: int,
    doc_type: str,
    embeddings_model_fn,  # Function that takes text and returns embedding vector
    chunk_id: int = 0,
    total_chunks: int = 1,
    section_title: str = None,
    source_file: str = None,
    source_url: str = None
) -> Optional[int]:
    """
    Embed narrative text and store in Qdrant, register in PostgreSQL
    
    Args:
        text: Narrative text to embed
        collection_name: Qdrant collection name
        company: Company name
        ticker: Stock ticker
        year: Fiscal year
        doc_type: Type of document (e.g., 'earnings_call', 'risk_factors')
        embeddings_model_fn: Function to generate embeddings
        chunk_id: Chunk sequence number
        total_chunks: Total chunks for this document
        section_title: Section title/heading
        source_file: Source file name
        source_url: Source URL if available
        
    Returns:
        PostgreSQL row ID of narrative_documents record, or None on failure
    """
    try:
        # Generate embedding
        embedding = embeddings_model_fn(text)
        
        # Store in Qdrant
        client = get_qdrant_client()
        point_id = int(uuid4().int % (2**63))  # Generate unique ID using UUID
        
        payload = {
            'company': company,
            'ticker': ticker,
            'year': year,
            'doc_type': doc_type,
            'section_title': section_title or '',
            'chunk_id': chunk_id,
            'summary': text[:200],  # First 200 chars as summary
        }
        
        from qdrant_client.models import PointStruct
        client.upsert(
            collection_name=collection_name,
            points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
        )
        
        # Register in PostgreSQL
        db_id = register_narrative_document(
            company=company,
            ticker=ticker,
            year=year,
            doc_type=doc_type,
            qdrant_point_id=point_id,
            qdrant_collection=collection_name,
            chunk_id=chunk_id,
            total_chunks=total_chunks,
            section_title=section_title,
            summary=text[:200],
            source_file=source_file,
            source_url=source_url
        )
        
        logger.debug(f"Stored narrative chunk: {doc_type} for {ticker} (Qdrant ID: {point_id})")
        return db_id
        
    except Exception as exc:
        logger.error(f"Failed to embed and store narrative: {exc}")
        return None
