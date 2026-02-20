#!/usr/bin/env python3
"""
Ingest narrative financial data (earnings transcripts) into Qdrant.

This script:
1. Fetches or loads earnings transcripts
2. Chunks narrative text
3. Generates embeddings
4. Stores in Qdrant with metadata
5. Registers in PostgreSQL

Phase 2: Hybrid Narrative Retrieval
"""
import sys
import os
from pathlib import Path
from typing import Optional

# Add backend to path (go up 4 levels from backend/app/data/scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.config import settings, DATA_OUTPUT_DIR
from app.data.adapter import (
    chunk_text,
    create_qdrant_collection_if_needed,
    embed_and_store_narrative,
)
from app.core.embeddings import embed_text
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Sample narrative data for demonstration
# In production, fetch from earnings_call_fetcher.py
SAMPLE_NARRATIVES = {
    "AAPL_2025_Q4": {
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "year": 2025,
        "quarter": 4,
        "doc_type": "earnings_transcript",
        "prepared_remarks": """
Apple Q4 2025 Prepared Remarks

Good afternoon, everyone, and thank you for joining us. I'm Tim Cook, CEO of Apple.

In Q4, we delivered record revenue of $119.6 billion, up 12% year-over-year. 
This was driven by strong iPhone 17 sales in China and Services reaching an all-time high.

Our gross margin expanded to 47.5%, up 60 basis points, reflecting improved
product mix and manufacturing efficiency. Operating income grew 18% to $36.2 billion.

Looking ahead, we see significant opportunities in AI integration with iOS 19,
the new Apple Watch with health sensors, and continued Services momentum.
Our installed base reached 2.2 billion devices worldwide.

For the full year 2025, we achieved revenue of $410.2 billion and net income of $114.3 billion.
Our return on equity reached 156%, among the highest in tech.

We remain committed to innovation, environmental sustainability, and returning capital
to shareholders. The Board approved a $150 billion share buyback authorization.
        """,
        "qa_section": """
Q&A SESSION

Q: Tim, can you discuss the outlook for AI revenue?
A: Absolutely. We believe AI will be transformative, particularly on-device AI which
preserves privacy. Our initial rollout of Apple Intelligence in iOS 18.3 saw strong
adoption. Revenue attributed to AI features could reach 15-20% of Services by 2026.
We're seeing good demand signals from enterprise and consumer segments.

Q: What about competitive pressures in China?
A: China remains critical, now representing 22% of revenue. While competition is intense,
our brand loyalty is strong, evidenced by 48% attach rates for Services in China.
We're localizing features and pricing strategically. Growth in China was 8% this year,
benefiting from the iPhone 17's strong camera and health features.

Q: Can you detail the iPhone 17 Pro performance?
A: The Pro models exceeded our expectations. Pro sales were up 24% YoY due to the new
titanium design and computational photography advances. Average selling price increased
to $1,120 due to Pro mix. We're seeing healthy demand in both developed and emerging
markets. Supply constraints have eased, giving us better positioning heading into 2026.

Q: What are the risks you're most concerned about?
A: Geopolitical uncertainty could impact supply chains, particularly in Taiwan.
Regulatory scrutiny on App Store practices continues in EU and elsewhere.
Macro uncertainty, while manageable now, could impact consumer spending. We're hedging
through Services growth, which is more resilient to hardware cycles.
        """
    },
    "MSFT_2025_Q4": {
        "ticker": "MSFT",
        "company": "Microsoft Corporation",
        "year": 2025,
        "quarter": 4,
        "doc_type": "earnings_transcript",
        "prepared_remarks": """
Microsoft Q4 2025 Prepared Remarks

Hello, and thank you for joining our Q4 2025 earnings call. This is Satya Nadella.

We had a strong quarter with total revenue of $72.5 billion, up 15% year-over-year.
Cloud revenue, including Azure and M365, grew 22%, reaching $38.2 billion.

Azure's momentum continued with 29% growth, driven by enterprise AI workloads.
We're seeing customers deploy large language models at scale. Our committed AI
infrastructure spending has attracted significant enterprise contracts.

Copilot adoption metrics are encouraging. Copilot Pro subscribers grew 180% to
4.2 million. Enterprise adoption of Copilot in Microsoft 365 reached 65% of
premium-tier accounts, up from 38% last year.

Gaming revenue improved with Strong demand for Starfield and new Game Pass content.
LinkedIn showed steady growth at 12% as recruitment spending rebounded.

Our AI initiatives position us well for continued cloud growth. The partnership
with OpenAI continues to deepen, and we're investing $6.5 billion annually in
AI infrastructure development through 2027.
        """,
        "qa_section": """
Q&A SESSION

Q: Satya, can you elaborate on enterprise AI adoption?
A: Enterprise deployment of AI agents is accelerating beyond our expectations.
We're seeing 45% of Fortune 500 companies actively running Copilot pilots in
production environments now. The financial services sector shows 52% adoption.
Revenue from enterprise AI services is on pace to exceed $8 billion by end of 2026.

Q: What's your outlook for Azure growth as AI normalizes?
A: Good question. We believe we're still in early innings for enterprise AI adoption.
The market is shifting from experimentation to production workloads. This favors
established providers like us with enterprise relationships and compliance certifications.
We see Azure growth remaining 20%+ through 2027 as AI-driven computing cycles mature.

Q: How do you view competition from open-source LLMs?
A: We've actually thrived with open source. Our Azure OpenSource initiative now
hosts hundreds of open models. We believe enterprises value our integrated stack,
support, and enterprise-grade security over pure commodity models.

Q: What are key risks?
A: Regulatory scrutiny around AI data usage is a key watch. Energy costs for
infrastructure are rising due to AI training demands. Macro uncertainty in Europe
persists, impacting at least 2-3 points of growth.
        """
    }
}


def load_sample_narratives() -> dict:
    """Load sample narrative data for demonstration."""
    return SAMPLE_NARRATIVES


def ingest_narrative(
    ticker: str,
    company: str,
    year: int,
    quarter: int,
    prepared_remarks: str,
    qa_section: str,
    collection_name: str = "financial_narratives"
) -> int:
    """
    Ingest a single company's earnings transcript into Qdrant.
    
    Args:
        ticker: Stock ticker
        company: Company name
        year: Fiscal year
        quarter: Quarter number
        prepared_remarks: Prepared remarks text
        qa_section: Q&A section text
        collection_name: Qdrant collection name
        
    Returns:
        Number of chunks successfully ingested
    """
    ingested = 0
    
    # Process prepared remarks
    if prepared_remarks and len(prepared_remarks.strip()) > 100:
        chunks = chunk_text(prepared_remarks, chunk_size=400, overlap=50)
        for idx, chunk in enumerate(chunks):
            try:
                embed_and_store_narrative(
                    text=chunk,
                    collection_name=collection_name,
                    company=company,
                    ticker=ticker,
                    year=year,
                    doc_type="earnings_transcript",
                    embeddings_model_fn=embed_text,
                    chunk_id=idx,
                    total_chunks=len(chunks),
                    section_title=f"Prepared Remarks (AAPL Q{quarter})",
                    source_file=f"{ticker}_earnings_q{quarter}_{year}.json"
                )
                ingested += 1
            except Exception as exc:
                logger.error(f"Failed to ingest chunk {idx}: {exc}")
    
    # Process Q&A section
    if qa_section and len(qa_section.strip()) > 100:
        chunks = chunk_text(qa_section, chunk_size=400, overlap=50)
        for idx, chunk in enumerate(chunks):
            try:
                embed_and_store_narrative(
                    text=chunk,
                    collection_name=collection_name,
                    company=company,
                    ticker=ticker,
                    year=year,
                    doc_type="earnings_transcript",
                    embeddings_model_fn=embed_text,
                    chunk_id=idx + len(chunks),  # Offset from prepared remarks
                    total_chunks=len(chunks),
                    section_title=f"Q&A Section (AAPL Q{quarter})",
                    source_file=f"{ticker}_earnings_q{quarter}_{year}.json"
                )
                ingested += 1
            except Exception as exc:
                logger.error(f"Failed to ingest Q&A chunk {idx}: {exc}")
    
    return ingested


def main():
    """Main ingestion workflow."""
    print("\n" + "="*70)
    print("Phase 2: Narrative Data Ingestion into Qdrant")
    print("="*70 + "\n")
    
    # Step 1: Create Qdrant collection
    print("📝 Step 1: Creating Qdrant collection...")
    if not create_qdrant_collection_if_needed("financial_narratives"):
        print("❌ Failed to create Qdrant collection")
        return False
    print("✅ Qdrant collection ready\n")
    
    # Step 2: Load narrative data
    print("📚 Step 2: Loading narrative data...")
    narratives = load_sample_narratives()
    print(f"✅ Loaded {len(narratives)} narrative sources\n")
    
    # Step 3: Ingest narratives
    print("🔄 Step 3: Ingesting narratives into Qdrant...")
    total_chunks = 0
    
    for key, narrative in narratives.items():
        ingest_key = f"{narrative['ticker']}_{narrative['year']}_Q{narrative['quarter']}"
        print(f"\n  Ingesting {ingest_key}...")
        
        chunks_ingested = ingest_narrative(
            ticker=narrative['ticker'],
            company=narrative['company'],
            year=narrative['year'],
            quarter=narrative['quarter'],
            prepared_remarks=narrative['prepared_remarks'],
            qa_section=narrative['qa_section']
        )
        
        total_chunks += chunks_ingested
        print(f"    ✅ {chunks_ingested} chunks ingested")
    
    print(f"\n✅ Ingestion complete: {total_chunks} chunks total\n")
    
    # Step 4: Verify with a test search
    print("🔍 Step 4: Verifying with test search...")
    try:
        from app.core.retrieval import retrieve_narrative_context
        from app.core.embeddings import embed_text
        
        test_query = "What is Apple's AI strategy?"
        test_embedding = embed_text(test_query)
        
        results = retrieve_narrative_context(
            query_embedding=test_embedding,
            tickers=["AAPL"],
            limit=3
        )
        
        if results:
            print(f"✅ Found {len(results)} relevant narrative chunks for test query\n")
            for i, chunk in enumerate(results, 1):
                print(f"   [{i}] {chunk['doc_type']} - {chunk['ticker']} FY{chunk['year']}")
                print(f"       Score: {chunk['score']:.3f}")
                print(f"       Section: {chunk['section_title']}\n")
        else:
            print("⚠️  No results found - Qdrant may be empty\n")
        
    except Exception as exc:
        logger.error(f"Verification failed: {exc}")
    
    print("="*70)
    print("Phase 2 Narrative Ingestion Complete")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
