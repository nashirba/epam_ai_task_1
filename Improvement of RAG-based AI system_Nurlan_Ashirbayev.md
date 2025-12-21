# Advanced RAG Practical Task: Improvement of RAG-based AI System

### [Github repository link](https://github.com/nashirba/epam_ai_task_1/tree/feature/RAG_assignment_2)

---

## Executive Summary

This document summarizes my work on evaluating and enhancing a RAG system for Diet & Nutrition Assistant. **The complete detailed report is available at:** [`COMPREHENSIVE_RAG_EVALUATION_REPORT.md`](./COMPREHENSIVE_RAG_EVALUATION_REPORT.md)

### Target Achieved: +31.6% Improvement in Recall@K

| Metric | Baseline | Enhanced | Improvement | Target |
|--------|----------|----------|-------------|--------|
| **Recall@K** | 70.7% | 93.0% | **+31.6%** | Achieved |
| Hit Rate | 80.0% | 86.0% | +7.5% | - |
| MRR | 0.800 | 0.807 | +0.8% | - |

---

## Evaluation Setup

### Dataset
- **72 documents** in knowledge base (expanded from 20)
- **50 test questions** across 9 categories (factual, inference, multi-document, edge cases, etc.)

### Configurations Compared

| Setting | Baseline | Enhanced |
|---------|----------|----------|
| Top-K | 1 | 5 |
| Search Type | Vector only | Hybrid (Vector + BM25) |
| Reranking | None | Cross-encoder (ms-marco-MiniLM-L-6-v2) |
| Fusion | None | Reciprocal Rank Fusion (k=60) |

---

## Enhancement Architecture

```
Query
  │
  ├─────────────┐
  ▼             ▼
Vector       BM25
Search       Search
  │             │
  └──────┬──────┘
         ▼
   Reciprocal Rank
      Fusion
         │
         ▼
   Cross-Encoder
     Reranking
         │
         ▼
    Final Results
```

---

## Key Results

### Why Recall@K Shows the Largest Improvement

**Recall@K** measures the proportion of all relevant documents that were successfully retrieved. The improvement from 70.7% to 93.0% (+31.6%) demonstrates that:

1. **Larger candidate pool (K=5)** captures more relevant documents
2. **Hybrid search** catches both semantic and lexical matches
3. **Multi-document queries benefit most** - questions requiring multiple sources now retrieve more of them

### Trade-offs

| Aspect | Change | Explanation |
|--------|--------|-------------|
| Latency | +48ms | Reranking adds computational overhead |
| Recall | +31.6% | Primary goal achieved |

---

## How to Run

```bash
# 1. Start Weaviate
docker-compose up -d weaviate

# 2. Load expanded dataset
cd /path/to/task_1
python scripts/data_loader.py --use-expanded --force-reload

# 3. Run comprehensive evaluation
python evaluation/run_comprehensive_evaluation.py --use-expanded-data
```

---

## Conclusion

The RAG enhancement techniques successfully achieved a **31.6% improvement in Recall@K**, exceeding the 30% target. The combination of hybrid search, cross-encoder reranking, and expanded candidate pools effectively addresses the limitations of pure vector search for multi-document queries.

---

📄 **For complete details, methodology, and analysis, see:** [`COMPREHENSIVE_RAG_EVALUATION_REPORT.md`](./COMPREHENSIVE_RAG_EVALUATION_REPORT.md)
