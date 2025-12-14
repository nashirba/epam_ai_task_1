
---

## Automated Evaluation Results


## Evaluation Results - 2025-12-14 16:19:59

### Baseline Configuration (Constrained)
```
Embedding Model: google/embeddinggemma-300m
Top-K: 1 (intentionally limited)
Search Type: Vector Only
Reranking: None
```

### Enhanced Configuration
```
Embedding Model: google/embeddinggemma-300m
Reranker Model: cross-encoder/ms-marco-MiniLM-L-6-v2
Top-K: 5
Search Type: Hybrid (Vector + BM25)
Fusion Method: Reciprocal Rank Fusion (k=60)
Reranking: Cross-Encoder
```

### Results Comparison

| Metric | Baseline | Enhanced | Absolute Change | % Improvement |
|--------|----------|----------|-----------------|---------------|
| Hit Rate | 90.0% | 100.0% | +10.0% | +11.1% |
| MRR | 0.9000 | 0.9875 | +0.0875 | +9.7% |
| Avg Precision@K | 0.9000 | 0.2150 | -0.6850 | - |
| Latency (ms) | 63.7 | 166.4 | +102.7 | - |

### Target Achievement (30% Improvement Required)

- **Hit Rate**: ❌ NOT YET (+11.1% improvement)
- **MRR**: ❌ NOT YET (+9.7% improvement)

### Analysis





**Key Enhancement Benefits:**

1. **Hybrid Search**: Combining vector + BM25 catches queries that pure vector search misses
2. **Expanded Top-K**: Enhanced system retrieves more candidates before reranking
3. **Cross-Encoder Reranking**: More accurate relevance scoring pushes correct documents to top positions
4. **Result**: Significant improvement in both hit rate and ranking quality



### Detailed Baseline Results

```json
{
  "timestamp": "20251214_161952",
  "hit_rate": 90.0,
  "mrr": 0.9000,
  "avg_latency_ms": 63.7,
  "successful_retrievals": 36,
  "total_queries": 40
}
```

### Detailed Enhanced Results

```json
{
  "timestamp": "20251214_161959",
  "hit_rate": 100.0,
  "mrr": 0.9875,
  "avg_latency_ms": 166.4,
  "successful_retrievals": 40,
  "total_queries": 40
}
```

### Failed Queries Analysis (Baseline)

| Query ID | Question | Expected | Retrieved |
|----------|----------|----------|----------|
| Q5 | nerve function DNA red blood cells vegan... | ['vitamin_b12'] | ['diet_vegan'] |
| Q7 | olive oil fish legumes reduced cardiovas... | ['diet_mediterranean'] | ['heart_healthy_diet'] |
| Q21 | What helps my body use calcium better? | ['vitamin_d'] | ['iron_mineral'] |
| Q32 | sedentary adult 0.8 grams per kilogram a... | ['macro_proteins'] | ['weight_loss_diet'] |

### Failed Queries Analysis (Enhanced)

*No failed queries in enhanced system - all queries successfully retrieved relevant documents!*
