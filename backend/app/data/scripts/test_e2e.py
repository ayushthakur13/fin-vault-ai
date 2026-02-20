#!/usr/bin/env python3
"""
End-to-End Test Script
Tests the complete hybrid retrieval + LLM reasoning workflow
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.retrieval import (
    perform_hybrid_retrieval,
    classify_query_mode,
    build_llm_prompt,
    format_context_for_llm
)
from app.core.embeddings import embed_text
from app.core.llm import quick_model_call
from app.utils.helpers import get_logger

logger = get_logger(__name__)


TEST_QUERIES = [
    ("Compare Apple and Microsoft revenue", ["AAPL", "MSFT"]),
    ("How has Apple's profit margin changed?", ["AAPL"]),
    ("Which company has better ROE?", ["AAPL", "MSFT"]),
]


def run_test_query(query: str, tickers: list = None, verbose: bool = True):
    """
    Execute a test query through the full pipeline
    """
    if verbose:
        print(f"\n{'='*80}")
        print(f"🔍 TEST QUERY: {query}")
        print(f"{'='*80}")
    
    try:
        # Step 1: Classify query
        mode = classify_query_mode(query)
        if verbose:
            print(f"[1] Query Mode: {mode}")
        
        # Step 2: Hybrid retrieval
        if verbose:
            print(f"[2] Performing hybrid retrieval...")
        
        context = perform_hybrid_retrieval(
            query=query,
            embeddings_model_fn=embed_text,
            tickers=tickers,
            force_mode=None
        )
        
        summary = context.get('retrieval_summary', {})
        if verbose:
            print(f"    - Numeric records: {summary.get('numeric_retrieved')}")
            print(f"    - Narrative chunks: {summary.get('narrative_retrieved')}")
            print(f"    - Retrieval latency: {summary.get('latency_ms')}ms")
        
        # Step 3: Format context
        if verbose:
            print(f"[3] Formatting context for LLM...")
        
        formatted_context = format_context_for_llm(context)
        if verbose:
            print(f"    - Context length: {len(formatted_context)} chars")
        
        # Step 4: Build prompt
        if verbose:
            print(f"[4] Building LLM prompt...")
        
        prompt = build_llm_prompt(query, context)
        if verbose:
            print(f"    - Prompt length: {len(prompt)} chars")
        
        # Step 5: Call LLM
        if verbose:
            print(f"[5] Calling Groq LLM (quick model)...")
        
        result = quick_model_call(prompt)
        analysis = result.get('output', '')
        is_mock = result.get('mock', False)
        
        if verbose:
            print(f"    - Model: {'llama-3.1-8b-instant'}")
            print(f"    - Mock response: {is_mock}")
            print(f"    - Response length: {len(analysis)} chars")
        
        # Step 6: Display results
        if verbose:
            print(f"\n{'─'*80}")
            print("ANALYSIS:")
            print(f"{'─'*80}")
            print(analysis)
            print(f"{'─'*80}\n")
        
        return {
            'success': True,
            'query': query,
            'mode': mode,
            'numeric_records': summary.get('numeric_retrieved'),
            'narrative_chunks': summary.get('narrative_retrieved'),
            'analysis': analysis,
            'mock': is_mock
        }
        
    except Exception as exc:
        logger.error(f"Test query failed: {exc}")
        if verbose:
            print(f"\n❌ ERROR: {exc}")
        
        return {
            'success': False,
            'query': query,
            'error': str(exc)
        }


def main():
    """Run end-to-end tests"""
    print("\n" + "="*80)
    print("🧪 FINVAULT AI - END-TO-END TEST")
    print("="*80)
    
    results = []
    
    for query, tickers in TEST_QUERIES:
        result = run_test_query(query, tickers, verbose=True)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r.get('success'))
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success') else "❌"
        query = result.get('query', 'unknown')[:50]
        
        if result.get('success'):
            metrics = result.get('numeric_records', 0)
            narrative = result.get('narrative_chunks', 0)
            print(f"{status} Test {i}: {query} ({metrics} metrics, {narrative} narratives)")
        else:
            error = result.get('error', 'unknown')
            print(f"{status} Test {i}: {query} - {error}")
    
    print(f"\n Summary: {successful}/{len(results)} tests passed")
    
    if successful == len(results):
        print("🎉 All tests passed! System is ready for queries.")
    else:
        print("⚠️  Some tests failed. Check logs above.")
    
    print("")


if __name__ == "__main__":
    main()
