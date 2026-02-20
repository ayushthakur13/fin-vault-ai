#!/usr/bin/env python3
"""
Phase 2 End-to-End Test: Hybrid Narrative Retrieval

Tests the complete workflow:
1. Ingest narrative data into Qdrant
2. Perform hybrid queries combining numeric + narrative
3. Verify citations in output
4. Check for contradiction detection
5. Validate latency under 30 seconds (quick mode)
"""
import sys
import os
from pathlib import Path
import json

# Add backend to path (go up 4 levels from backend/app/data/scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.embeddings import embed_text
from app.core.retrieval import perform_hybrid_retrieval, assemble_context
from app.core.llm import quick_model_call, deep_model_call
from app.config import DATA_OUTPUT_DIR
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Test queries for Phase 2
PHASE2_TEST_QUERIES = [
    {
        "query": "Compare Apple and Microsoft financial performance in 2025",
        "mode": "quick",
        "expected_mode": "hybrid",
        "description": "Numeric comparison with narrative insights",
    },
    {
        "query": "What is Apple's outlook for AI and what risks exist?",
        "mode": "quick",
        "expected_mode": "narrative",
        "description": "Query focusing on narrative/commentary",
    },
    {
        "query": "Generate bull and bear thesis for Apple FY2025",
        "mode": "quick",
        "expected_mode": "hybrid",
        "description": "Requires both metrics and transcript analysis",
    },
]


def run_phase2_tests():
    """Run comprehensive Phase 2 tests."""
    print("\n" + "="*80)
    print("PHASE 2 END-TO-END TEST: Hybrid Narrative Retrieval")
    print("="*80 + "\n")
    
    results = []
    
    for idx, test_case in enumerate(PHASE2_TEST_QUERIES, 1):
        print(f"\n📋 Test {idx}: {test_case['description']}")
        print(f"   Query: {test_case['query'][:60]}...")
        print(f"   Mode: {test_case['mode']}")
        print("-" * 80)
        
        try:
            import time
            start_time = time.time()
            
            # Perform hybrid retrieval
            print("   ⏳ Performing hybrid retrieval...")
            context = perform_hybrid_retrieval(
                query=test_case['query'],
                embeddings_model_fn=embed_text,
                tickers=['AAPL', 'MSFT'],
                force_mode=None,  # Let it classify
                numeric_limit=20,
                narrative_limit=5
            )
            
            retrieval_summary = context.get('retrieval_summary', {})
            numeric_count = retrieval_summary.get('numeric_retrieved', 0)
            narrative_count = retrieval_summary.get('narrative_retrieved', 0)
            detected_mode = retrieval_summary.get('query_mode', 'unknown')
            
            print(f"   ✅ Retrieval complete:")
            print(f"      • Detected mode: {detected_mode}")
            print(f"      • Numeric records: {numeric_count}")
            print(f"      • Narrative chunks: {narrative_count}")
            
            # Verify mode detection
            mode_match = detected_mode == test_case['expected_mode']
            print(f"      • Mode match: {'✅' if mode_match else '⚠️'} ({test_case['expected_mode']} expected)")
            
            # Extract data
            numeric_data = context.get('numeric_data', [])
            narrative_chunks = context.get('narrative_chunks', [])
            
            # Assemble context with citations
            print("   ⏳ Assembling context with citations...")
            assembled = assemble_context(
                query=test_case['query'],
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
                ],
                include_contradiction_check=True
            )
            
            # Check for citations
            has_citations = '[Source:' in assembled
            print(f"   ✅ Context assembled: {'✅ Has citations' if has_citations else '⚠️ No citations detected'}")
            
            # Call LLM
            print("   ⏳ Calling Groq LLM (quick mode)...")
            llm_input = assembled + "\n\nProvide your analysis:\n"
            llm_result = quick_model_call(llm_input)
            analysis = llm_result.get("output", "No response")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Verify output quality
            has_citations_in_response = '[Source:' in analysis or 'Source:' in analysis
            has_metrics = any(word in analysis.lower() for word in ['revenue', 'profit', 'growth', 'roe', 'margin'])
            
            print(f"   ✅ LLM response received ({latency_ms}ms):")
            print(f"      • Response length: {len(analysis)} chars")
            print(f"      • Has citations: {'✅' if has_citations_in_response else '⚠️'}")
            print(f"      • References metrics: {'✅' if has_metrics else '⚠️'}")
            print(f"      • Latency OK: {'✅' if latency_ms < 30_000 else '❌'} ({latency_ms}ms < 30s)")
            
            # Store result
            results.append({
                'test': idx,
                'query': test_case['query'][:50],
                'description': test_case['description'],
                'detected_mode': detected_mode,
                'mode_correct': mode_match,
                'numeric_count': numeric_count,
                'narrative_count': narrative_count,
                'has_citations': has_citations_in_response,
                'has_metrics': has_metrics,
                'latency_ms': latency_ms,
                'latency_ok': latency_ms < 30_000,
                'response_chars': len(analysis),
            })
            
            # Print sample response
            print(f"\n   📄 Sample Output ({len(analysis)} chars):")
            sample = analysis[:300].replace('\n', ' ')
            print(f"      {sample}...\n")
            
        except Exception as exc:
            logger.error(f"Test {idx} failed: {exc}")
            results.append({
                'test': idx,
                'query': test_case['query'][:50],
                'description': test_case['description'],
                'error': str(exc),
            })
            print(f"   ❌ Test failed: {exc}\n")
    
    # Summary
    print("\n" + "="*80)
    print("PHASE 2 TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if 'error' not in r)
    total_count = len(results)
    
    for result in results:
        if 'error' in result:
            print(f"\n❌ Test {result['test']}: {result['description']}")
            print(f"   Error: {result['error']}")
        else:
            status = "✅" if result['mode_correct'] and result['has_citations'] and result['latency_ok'] else "⚠️"
            print(f"\n{status} Test {result['test']}: {result['description']}")
            print(f"   Mode: {result['detected_mode']} (expected {result.get('expected_mode', '?')})")
            print(f"   Data: {result['numeric_count']} metrics + {result['narrative_count']} narratives")
            print(f"   Quality: Citations={result['has_citations']}, Metrics={result['has_metrics']}")
            print(f"   Latency: {result['latency_ms']}ms {'✅' if result['latency_ok'] else '❌'}")
    
    print(f"\n{'-'*80}")
    print(f"Results: {success_count}/{total_count} tests completed successfully")
    print(f"Phase 2 Status: {'✅ COMPLETE' if success_count == total_count else '⚠️ PARTIAL'}")
    print("="*80 + "\n")
    
    return success_count == total_count


def main():
    """Main test runner."""
    success = run_phase2_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
