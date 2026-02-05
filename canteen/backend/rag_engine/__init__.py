"""
RAG Engine Package (OPTIONAL)

⚠️  This is an OPTIONAL module for advanced use cases.
    Most applications should use the rule-based engine.

Usage:
------
    # Check if RAG is available
    from rag_engine import RAG_AVAILABLE
    
    if RAG_AVAILABLE:
        from rag_engine import get_rag_engine, get_hybrid_engine
        
        # Use RAG engine
        engine = get_rag_engine()
        
        # Or use hybrid approach
        hybrid = get_hybrid_engine()

Prerequisites:
--------------
    pip install sentence-transformers faiss-cpu

Cost Warning:
-------------
    RAG engines may incur costs if using paid embedding services.
    Always test with free/local models first.
"""

from .rag_engine import (
    RAG_AVAILABLE,
    RAGRecommendationEngine,
    HybridRecommendationEngine,
    get_rag_engine,
    get_hybrid_engine
)

__all__ = [
    'RAG_AVAILABLE',
    'RAGRecommendationEngine',
    'HybridRecommendationEngine',
    'get_rag_engine',
    'get_hybrid_engine'
]
__version__ = '0.1.0'
__status__ = 'Experimental'
