"""
LangGraph Agent Definition
Minimal orchestration of retrieval → reasoning → formatting
"""
from typing import TypedDict, Optional
from langgraph.graph import END, StateGraph

from app.core.retrieval import (
    perform_hybrid_retrieval,
    build_llm_prompt,
    format_context_for_llm,
    HybridContext
)
from app.core.embeddings import embed_text
from app.core.llm import quick_model_call, deep_model_call
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class GraphState(TypedDict, total=False):
    """Agent state maintained across graph execution"""
    query: str
    mode: str  # 'quick' or 'deep'
    tickers: Optional[list[str]]
    retrieval_context: HybridContext
    raw_analysis: str
    formatted_response: str
    error: Optional[str]


def retrieve_node(state: GraphState) -> GraphState:
    """
    Retrieval node: Fetch numeric + narrative data
    """
    try:
        logger.info(f"[RETRIEVE] Processing: {state['query'][:50]}...")
        
        context = perform_hybrid_retrieval(
            query=state['query'],
            embeddings_model_fn=embed_text,
            tickers=state.get('tickers'),
            force_mode=None  # Auto-classify
        )
        
        state['retrieval_context'] = context
        
        logger.info(
            f"[RETRIEVE] Retrieved {len(context.get('numeric_data', []))} "
            f"metrics + {len(context.get('narrative_chunks', []))} narrative chunks"
        )
        
    except Exception as exc:
        logger.error(f"[RETRIEVE] Failed: {exc}")
        state['error'] = str(exc)
    
    return state


def reasoning_node(state: GraphState) -> GraphState:
    """
    Reasoning node: Send context + query to LLM
    """
    try:
        if state.get('error'):
            return state
        
        context = state.get('retrieval_context', {})
        logger.info("[REASON] Building prompt and calling LLM...")
        
        # Build prompt
        prompt = build_llm_prompt(
            query=state['query'],
            context=context,
            system_role="financial research assistant"
        )
        
        # Call appropriate model
        is_deep_mode = state.get('mode') == 'deep'
        model_fn = deep_model_call if is_deep_mode else quick_model_call
        
        result = model_fn(prompt)
        state['raw_analysis'] = result.get('output', '')
        
        logger.info(f"[REASON] Generated analysis ({len(state['raw_analysis'])} chars)")
        
    except Exception as exc:
        logger.error(f"[REASON] Failed: {exc}")
        state['error'] = str(exc)
    
    return state


def format_node(state: GraphState) -> GraphState:
    """
    Format node: Structure response with metadata
    """
    try:
        if state.get('error'):
            return state
        
        logger.info("[FORMAT] Formatting response...")
        
        context = state.get('retrieval_context', {})
        summary = context.get('retrieval_summary', {})
        
        formatted = {
            'analysis': state.get('raw_analysis', ''),
            'retrieval_mode': summary.get('query_mode', 'unknown'),
            'numeric_records': summary.get('numeric_retrieved', 0),
            'narrative_chunks': summary.get('narrative_retrieved', 0),
            'retrieval_latency_ms': summary.get('latency_ms', 0),
            'context_summary': format_context_for_llm(context)[:500]  # First 500 chars
        }
        
        state['formatted_response'] = str(formatted)
        logger.info("[FORMAT] Response formatted")
        
    except Exception as exc:
        logger.error(f"[FORMAT] Failed: {exc}")
        state['error'] = str(exc)
    
    return state


def build_graph():
    """
    Build LangGraph state machine for financial reasoning
    
    Flow: retrieve → reason → format → end
    """
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("reason", reasoning_node)
    graph.add_node("format", format_node)
    
    # Define edges
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "reason")
    graph.add_edge("reason", "format")
    graph.add_edge("format", END)
    
    return graph.compile()
