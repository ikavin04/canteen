# RAG Engine - Optional AI-Powered Recommendations

⚠️ **EXPERIMENTAL MODULE - NOT REQUIRED FOR PRODUCTION**

## Overview

This module provides AI-powered recommendations using Retrieval Augmented Generation (RAG). It's designed as an **optional upgrade** to the rule-based engine, not a replacement.

## When to Use RAG

✅ **Use RAG when:**
- Menu size exceeds 500+ items
- Need personalized recommendations based on user history
- Handling complex dietary restrictions
- Natural language queries required

❌ **Don't use RAG when:**
- Small menu (< 100 items) - use rule-based engine
- Latency requirements < 50ms
- Limited API budget
- Production system without extensive testing

## Installation

```bash
# Install optional dependencies
pip install sentence-transformers faiss-cpu

# For GPU acceleration (optional)
pip install faiss-gpu
```

## Usage

### Basic RAG

```python
from rag_engine import RAG_AVAILABLE, get_rag_engine

if RAG_AVAILABLE:
    engine = get_rag_engine()
    recommendations = engine.get_recommendations(
        cart_items=['Tea', 'Samosa'],
        available_items=menu_items
    )
```

### Hybrid Approach (Recommended)

```python
from rag_engine import get_hybrid_engine

# Combines rule-based + RAG for best results
engine = get_hybrid_engine()
recommendations = engine.get_recommendations(
    cart_items=['Tea', 'Samosa'],
    available_items=menu_items
)
```

## Architecture

1. **Embedding Generation**: Convert food knowledge to vectors
2. **Vector Storage**: Store in FAISS index
3. **Semantic Search**: Find similar items using cosine similarity
4. **LLM Formatting**: Use LLM only for response formatting (NOT decisions)

## Performance Considerations

| Aspect | Rule-Based | RAG |
|--------|-----------|-----|
| Latency | < 10ms | 50-200ms |
| Memory | < 1MB | 100-500MB |
| Accuracy | 95%+ | 85-90% |
| Cost | Free | API costs |

## Cost Estimation

- **Embeddings**: One-time cost ($0.0001 per 1K tokens)
- **Vector DB**: Memory only (free with FAISS)
- **LLM calls**: $0.002 per 1K tokens (if using)

For 100 items, total setup cost: ~$0.01

## Limitations

1. **Not Deterministic**: Results may vary between runs
2. **Higher Latency**: 10-20x slower than rule-based
3. **More Complex**: Harder to debug and maintain
4. **Resource Intensive**: Requires more memory

## Design Philosophy

**LLMs should enhance, not replace, business logic.**

This module uses AI for:
- ✅ Semantic similarity matching
- ✅ Response formatting
- ✅ Handling edge cases

This module does NOT use AI for:
- ❌ Core recommendation decisions
- ❌ Availability checking
- ❌ Price calculations
- ❌ Business rules

## Testing

```bash
# Test RAG engine
python -m pytest tests/test_rag_engine.py

# Benchmark performance
python -m rag_engine.benchmark
```

## Migration Path

```
Phase 1: Rule-Based Engine (Current)
   ↓
Phase 2: Hybrid (Rule + RAG for complex cases)
   ↓
Phase 3: Full RAG (Only if needed)
```

## Support

This module is experimental. For production use, stick with rule-based engine.

For questions: [Your Contact]
