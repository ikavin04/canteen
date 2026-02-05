"""
RAG-Based Recommendation Engine (OPTIONAL MODULE - EXPERIMENTAL)

⚠️  WARNING: This module is OPTIONAL and EXPERIMENTAL
    Only use this when rule-based recommendations are insufficient.

This module provides AI-powered recommendations using Retrieval Augmented Generation (RAG).

When to Use RAG:
----------------
1. Menu size > 500 items (too many rules to maintain)
2. Need personalized recommendations based on user history
3. Complex dietary restrictions and preferences
4. Natural language queries ("What goes with my meal?")

When NOT to Use:
----------------
1. Small menu (< 100 items) - use rule-based engine
2. Latency-critical applications (< 50ms response time)
3. Limited budget (LLM API costs)
4. Production systems without extensive testing

Architecture:
-------------
1. Load food knowledge base
2. Convert to embeddings using sentence-transformers
3. Store in FAISS vector database
4. Query similar items based on cart contents
5. Use LLM ONLY for formatting, NOT for decisions

Dependencies (NOT INCLUDED BY DEFAULT):
----------------------------------------
pip install sentence-transformers faiss-cpu openai chromadb

Cost Considerations:
--------------------
- Embeddings: One-time cost, can cache
- LLM calls: Pay per token, consider rate limits
- Vector DB: Memory overhead for large catalogs

Author: Smart Canteen Team
Version: 0.1.0 (Experimental)
Status: NOT PRODUCTION READY
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# NOTE: These imports will fail if dependencies are not installed
# This is intentional - we don't want to force users to install them
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG dependencies not installed. Using rule-based engine only.")
    print("To enable RAG: pip install sentence-transformers faiss-cpu")


class RAGRecommendationEngine:
    """
    Experimental RAG-based recommendation engine.
    
    This uses embeddings and semantic search to find relevant recommendations.
    It's more flexible than rule-based but requires more resources.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize RAG engine."""
        if not RAG_AVAILABLE:
            raise ImportError(
                "RAG dependencies not installed. "
                "Run: pip install sentence-transformers faiss-cpu"
            )
        
        if data_dir is None:
            current_dir = Path(__file__).parent
            data_dir = current_dir.parent / 'data'
        
        self.data_dir = Path(data_dir)
        self.knowledge_base = self._load_knowledge_base()
        self.model = None
        self.index = None
        self._initialize_embeddings()
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load structured food knowledge."""
        kb_file = self.data_dir / 'food_knowledge.json'
        
        if not kb_file.exists():
            print(f"Warning: Knowledge base not found at {kb_file}")
            return []
        
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return []
    
    def _initialize_embeddings(self):
        """
        Initialize the embedding model and vector index.
        
        This is expensive - only do it once at startup.
        """
        print("Initializing RAG engine (this may take a minute)...")
        
        # Use a lightweight model for speed
        # In production, consider: 'all-MiniLM-L6-v2' (fast) or 'all-mpnet-base-v2' (accurate)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create text corpus from knowledge base
        texts = []
        for item in self.knowledge_base:
            # Combine all fields into a rich text representation
            text = f"{item['item']} - {item['type']} - {item['taste_profile']} - " \
                   f"{item['reason']} - Pairs with: {', '.join(item['pairs_well_with'])}"
            texts.append(text)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} items...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.index.add(embeddings.astype('float32'))
        
        print("RAG engine initialized successfully!")
    
    def get_recommendations(
        self,
        cart_items: List[str],
        available_items: List[Dict[str, Any]],
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations using semantic search.
        
        Args:
            cart_items: List of item names in cart
            available_items: List of available menu items
            max_recommendations: Max items to return
            
        Returns:
            List of recommended items
        """
        if not cart_items or not self.model or not self.index:
            return []
        
        # Create query from cart items
        query = f"Food items that pair well with {', '.join(cart_items)}"
        query_embedding = self.model.encode([query])
        
        # Search vector database
        k = min(max_recommendations * 2, len(self.knowledge_base))
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Build recommendations
        recommendations = []
        cart_items_lower = [item.lower() for item in cart_items]
        
        for idx in indices[0]:
            if idx < len(self.knowledge_base):
                kb_item = self.knowledge_base[idx]
                item_name = kb_item['item']
                
                # Skip if already in cart
                if item_name.lower() in cart_items_lower:
                    continue
                
                # Find matching menu item
                menu_item = None
                for mi in available_items:
                    if mi.get('item_name', '').lower() == item_name.lower():
                        menu_item = mi
                        break
                
                if menu_item and menu_item.get('availability', False):
                    recommendations.append({
                        'item_id': menu_item.get('id'),
                        'item_name': menu_item.get('item_name'),
                        'price': float(menu_item.get('price', 0)),
                        'category': menu_item.get('category', ''),
                        'description': menu_item.get('description', ''),
                        'reason': kb_item.get('reason', 'Recommended based on your selection'),
                        'source': 'RAG'
                    })
                
                if len(recommendations) >= max_recommendations:
                    break
        
        return recommendations


# Optional: Hybrid engine that combines rule-based and RAG
class HybridRecommendationEngine:
    """
    Combines rule-based and RAG approaches.
    
    Strategy:
    1. Get rule-based recommendations (fast, reliable)
    2. Get RAG recommendations (semantic, flexible)
    3. Merge and deduplicate
    4. Score based on both methods
    """
    
    def __init__(self):
        """Initialize both engines."""
        from .rule_engine import RecommendationEngine
        
        self.rule_engine = RecommendationEngine()
        
        if RAG_AVAILABLE:
            try:
                self.rag_engine = RAGRecommendationEngine()
            except Exception as e:
                print(f"Failed to initialize RAG engine: {e}")
                self.rag_engine = None
        else:
            self.rag_engine = None
    
    def get_recommendations(
        self,
        cart_items: List[str],
        available_items: List[Dict[str, Any]],
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """Get hybrid recommendations."""
        # Always get rule-based recommendations
        rule_recs = self.rule_engine.get_recommendations(
            cart_items, available_items, max_recommendations
        )
        
        # Try to get RAG recommendations if available
        rag_recs = []
        if self.rag_engine:
            try:
                rag_recs = self.rag_engine.get_recommendations(
                    cart_items, available_items, max_recommendations
                )
            except Exception as e:
                print(f"RAG recommendation failed: {e}")
        
        # Merge results (prefer rule-based for duplicates)
        seen_ids = set()
        merged = []
        
        for rec in rule_recs:
            item_id = rec.get('item_id')
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                rec['source'] = 'rule-based'
                merged.append(rec)
        
        for rec in rag_recs:
            item_id = rec.get('item_id')
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                merged.append(rec)
        
        return merged[:max_recommendations]


def get_rag_engine():
    """Get RAG engine instance (if available)."""
    if not RAG_AVAILABLE:
        raise ImportError(
            "RAG not available. Install: pip install sentence-transformers faiss-cpu"
        )
    return RAGRecommendationEngine()


def get_hybrid_engine():
    """Get hybrid engine instance."""
    return HybridRecommendationEngine()
