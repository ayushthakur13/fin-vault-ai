"""
FinVault AI - Data Pipeline Integration Module
Bridges raw financial data from SEC/yfinance to AI agent
"""
from .adapter import (
    ingest_bulk_download_data,
    load_annual_csv_to_metrics,
    chunk_text,
    embed_and_store_narrative,
    create_qdrant_collection_if_needed
)

__all__ = [
    'ingest_bulk_download_data',
    'load_annual_csv_to_metrics',
    'chunk_text',
    'embed_and_store_narrative',
    'create_qdrant_collection_if_needed'
]
