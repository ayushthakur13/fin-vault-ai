#!/usr/bin/env python3
"""
Data Ingestion Script
Initializes PostgreSQL schema and ingests pipeline output data
Run this after bulk_download.py to populate the AI system with data
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.schema import init_schema
from app.data.adapter import (
    ingest_bulk_download_data,
    create_qdrant_collection_if_needed
)
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def main():
    """Main ingestion workflow"""
    print("\n" + "="*80)
    print("📊 FINVAULT AI - DATA INGESTION")
    print("="*80)
    
    # Step 1: Initialize PostgreSQL schema
    print("\n[1/3] Initializing PostgreSQL schema...")
    if init_schema():
        print("✅ PostgreSQL schema initialized")
    else:
        print("❌ Failed to initialize PostgreSQL schema")
        print("   Make sure DATABASE_URL is set and database is accessible")
        return
    
    # Step 2: Ingest bulk download CSV data
    print("\n[2/3] Ingesting financial metrics from bulk_download/...")
    summary = ingest_bulk_download_data()
    
    if not summary.get('success'):
        print("⚠️  No data ingested")
    else:
        total_inserted = sum(
            co['records_inserted'] 
            for co in summary.get('companies', {}).values()
        )
        print(f"✅ Ingested {total_inserted} financial metric records")
        
        for ticker, stats in summary.get('companies', {}).items():
            status = "✓" if stats['success'] else "✗"
            print(f"   {status} {ticker}: {stats['records_inserted']} records")
    
    # Step 3: Prepare Qdrant collection
    print("\n[3/3] Preparing Qdrant vector storage...")
    if create_qdrant_collection_if_needed("financial_narratives"):
        print("✅ Qdrant collection ready for narrative embeddings")
    else:
        print("⚠️  Could not initialize Qdrant collection")
        print("   (This is optional - proceed without narrative search)")
    
    print("\n" + "="*80)
    print("📈 INGESTION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Test with: python3 -m backend.app.api.test_query")
    print("  2. Or start the server: uvicorn backend.app.main:app --reload")
    print("  3. POST to /query endpoint with your financial queries")
    print("")


if __name__ == "__main__":
    main()
