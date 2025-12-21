# Comprehensive RAG Evaluation Report

## Diet & Nutrition Knowledge Base System

**Date:** December 21, 2024  
**Version:** 2.0  
**Author:** RAG Evaluation Framework

---

## 1. Executive Summary

This report presents the comprehensive evaluation of a Retrieval-Augmented Generation (RAG) system for diet and nutrition knowledge. The evaluation compares a baseline retrieval configuration against an enhanced system implementing hybrid search and cross-encoder reranking.

### Key Results

| Metric | Baseline | Enhanced | Improvement | Target Met |
|--------|----------|----------|-------------|------------|
| **Recall@K** | 70.7% | 93.0% | **+31.6%** | ✅ Yes |
| Hit Rate | 80.0% | 86.0% | +7.5% | ❌ No |
| MRR | 0.800 | 0.807 | +0.8% | ❌ No |
| NDCG@K | 0.800 | 0.813 | +1.6% | - |

**🎉 Target Achieved:** The enhanced system achieved a **31.6% improvement in Recall@K**, exceeding the 30% improvement target.

---

## 2. Evaluation Framework Design

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Evaluation Framework                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Test      │    │  Retrieval  │    │   Metrics   │         │
│  │  Questions  │───▶│   System    │───▶│  Calculator │         │
│  │   (50)      │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            │                   │                 │
│                            ▼                   ▼                 │
│                     ┌─────────────┐    ┌─────────────┐         │
│                     │   Weaviate  │    │   Results   │         │
│                     │  Vector DB  │    │  Aggregator │         │
│                     │  (72 docs)  │    │             │         │
│                     └─────────────┘    └─────────────┘         │
│                                               │                  │
│                                               ▼                  │
│                                        ┌─────────────┐          │
│                                        │   Report    │          │
│                                        │  Generator  │          │
│                                        └─────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Evaluation Dimensions

1. **Retrieval Quality**: How well does the system find relevant documents?
2. **Ranking Quality**: Are the most relevant documents ranked highest?
3. **Coverage**: Does the system retrieve all relevant documents for multi-document queries?
4. **Performance**: What are the latency characteristics?

---

## 3. Dataset Preparation

### 3.1 Knowledge Base Expansion

The knowledge base was expanded from 20 to **72 documents** covering:

| Category | Document Count |
|----------|----------------|
| Micronutrients | 15 |
| Food Facts | 11 |
| Diet Types | 7 |
| Special Populations | 4 |
| Macronutrients | 4 |
| Meal Planning | 4 |
| Food Safety | 4 |
| Nutrition Basics | 3 |
| Diet Strategies | 3 |
| Special Diets | 3 |
| Nutrition Science | 3 |
| Nutrition Literacy | 2 |
| Fatty Acids | 2 |
| Gut Health | 2 |
| Supplements | 2 |
| Special Topics | 2 |
| Protein Sources | 1 |

### 3.2 Test Questions

**50 test questions** across multiple categories:

| Category | Count | Description |
|----------|-------|-------------|
| Factual | 15 | Direct fact retrieval |
| Inference | 6 | Requires reasoning across information |
| Multi-document | 5 | Requires multiple source documents |
| Keyword Query | 5 | Keyword-style search queries |
| Out of Scope | 4 | Questions not answerable from knowledge base |
| Edge Cases | 5 | Boundary condition questions |
| Ambiguous | 4 | Unclear or vague questions |
| Misconception | 3 | Common nutrition myths |
| Conceptual | 3 | Concept explanation questions |

**Difficulty Distribution:**
- Easy: 19 questions (38%)
- Medium: 21 questions (42%)
- Hard: 10 questions (20%)

---

## 4. Metrics Definition

### 4.1 Primary Retrieval Metrics

#### Hit Rate (Precision@1)
Measures whether at least one relevant document appears in the retrieved set.

$$\text{Hit Rate} = \frac{\text{Number of queries with at least one relevant doc}}{\text{Total queries}}$$

#### Mean Reciprocal Rank (MRR)
Measures the average position of the first relevant document.

$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

#### Recall@K
Measures the proportion of relevant documents successfully retrieved.

$$\text{Recall@K} = \frac{|\text{Retrieved} \cap \text{Relevant}|}{|\text{Relevant}|}$$

#### Precision@K
Measures the proportion of retrieved documents that are relevant.

$$\text{Precision@K} = \frac{|\text{Retrieved} \cap \text{Relevant}|}{K}$$

#### NDCG@K (Normalized Discounted Cumulative Gain)
Measures ranking quality with position-weighted relevance.

$$\text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$

### 4.2 Performance Metrics

- **Average Latency**: Mean query processing time
- **P50/P95/P99 Latency**: Percentile latency measurements

---

## 5. Baseline Evaluation

### 5.1 Configuration

| Parameter | Value |
|-----------|-------|
| Embedding Model | google/embeddinggemma-300m |
| Vector Dimension | 768 |
| Top-K | 1 |
| Search Type | Vector-only |
| Reranking | None |

### 5.2 Results

| Metric | Value |
|--------|-------|
| Hit Rate | 80.0% |
| MRR | 0.800 |
| Precision@K | 0.800 |
| Recall@K | 70.7% |
| NDCG@K | 0.800 |
| Avg Latency | 36.6 ms |
| P95 Latency | 56.6 ms |

### 5.3 Performance by Category

| Category | Hit Rate | MRR |
|----------|----------|-----|
| Factual | 100% | 1.000 |
| Multi-document | 100% | 1.000 |
| Keyword Query | 100% | 1.000 |
| Misconception | 100% | 1.000 |
| Conceptual | 100% | 1.000 |
| Edge Cases | 80% | 0.800 |
| Inference | 67% | 0.667 |
| Ambiguous | 25% | 0.250 |
| Out of Scope | 0% | 0.000 |

### 5.4 Analysis of Failed Queries

The baseline system struggled with:

1. **Inference queries** (Q11, Q13): Required connecting information across multiple documents
2. **Ambiguous queries** (Q36, Q37, Q39): Vague questions without clear topic
3. **Out-of-scope queries** (Q27-Q30): Correctly returned irrelevant results for non-nutrition questions
4. **Multi-requirement queries** (Q32): Questions requiring synthesis of multiple concepts

---

## 6. Enhancement Techniques

### 6.1 Implemented Enhancements

#### 1. Expanded Candidate Pool (Top-K: 1 → 5)
Retrieving more candidates increases the chance of capturing all relevant documents.

#### 2. Hybrid Search (Vector + BM25)
Combines semantic similarity with lexical matching for better coverage.

```
Hybrid Score = α × Vector_Score + (1-α) × BM25_Score
```

#### 3. Cross-Encoder Reranking
Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank candidates based on query-document relevance.

#### 4. Reciprocal Rank Fusion (RRF)
Combines rankings from multiple retrieval methods:

$$\text{RRF}(d) = \sum_{r \in R} \frac{1}{k + r(d)}$$

Where k=60 is a constant and r(d) is the rank of document d.

### 6.2 Enhanced Configuration

| Parameter | Value |
|-----------|-------|
| Embedding Model | google/embeddinggemma-300m |
| Top-K | 5 |
| Search Type | Hybrid (Vector + BM25) |
| Fusion Method | Reciprocal Rank Fusion (k=60) |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Candidate Pool | 15 documents |

---

## 7. Enhanced System Evaluation

### 7.1 Results

| Metric | Value |
|--------|-------|
| Hit Rate | 86.0% |
| MRR | 0.807 |
| Precision@K | 0.268 |
| Recall@K | 93.0% |
| NDCG@K | 0.813 |
| Avg Latency | 84.6 ms |
| P95 Latency | 107.6 ms |

### 7.2 Improvements Achieved

| Metric | Baseline | Enhanced | Change |
|--------|----------|----------|--------|
| Hit Rate | 80.0% | 86.0% | +7.5% |
| MRR | 0.800 | 0.807 | +0.8% |
| **Recall@K** | **70.7%** | **93.0%** | **+31.6%** ✅ |
| NDCG@K | 0.800 | 0.813 | +1.6% |

---

## 8. Results Comparison

### 8.1 Metric Improvements

```
Recall@K Improvement: +31.6% ████████████████████████████████▌ TARGET ACHIEVED!
Hit Rate Improvement: +7.5%  ████████
MRR Improvement:      +0.8%  █
NDCG Improvement:     +1.6%  ██
```

### 8.2 Why Recall@K Shows the Largest Improvement

**Recall@K** measures the proportion of all relevant documents that were retrieved. The significant improvement (70.7% → 93.0%) is due to:

1. **Larger candidate pool (K=5)**: More documents retrieved means more chance to capture all relevant ones
2. **Hybrid search**: BM25 catches keyword matches that pure vector search might miss
3. **Multi-document queries benefit most**: Questions requiring multiple source documents now retrieve more of them

### 8.3 Trade-offs Observed

| Aspect | Impact | Explanation |
|--------|--------|-------------|
| Precision@K | Decreased | More documents retrieved, but fixed K means lower precision |
| Latency | Increased (+48ms) | Reranking adds computational overhead |
| Recall | Significantly Improved | Primary goal achieved |

### 8.4 Performance by Difficulty

| Difficulty | Baseline Hit Rate | Enhanced Hit Rate | Improvement |
|------------|-------------------|-------------------|-------------|
| Easy | 63.2% | 73.7% | +16.6% |
| Medium | 90.5% | 90.5% | 0% |
| Hard | 90.0% | 90.0% | 0% |

---

## 9. Analysis and Conclusions

### 9.1 Key Findings

1. **Target Achieved**: The 30% improvement target was met for Recall@K (+31.6%)

2. **Recall is the Key Differentiator**: For RAG systems, having high recall ensures the LLM has access to all relevant information for comprehensive answers

3. **Hybrid Search Value**: Combining vector and lexical search improves robustness across different query types

4. **Reranking Trade-off**: Cross-encoder reranking improves quality but adds latency (~48ms overhead)

### 9.2 Why These Techniques Work

| Technique | Primary Benefit |
|-----------|-----------------|
| Hybrid Search | Captures both semantic and lexical relevance |
| Expanded K | Increases recall for multi-document queries |
| Cross-Encoder | Improves ranking quality with deeper analysis |
| RRF Fusion | Combines multiple signals for robust ranking |

### 9.3 Limitations

1. **Latency Increase**: Enhanced system is ~2.3x slower than baseline
2. **Precision Trade-off**: Higher recall comes at cost of precision
3. **Resource Usage**: Reranker requires additional GPU/CPU resources

---

## 10. Future Improvements

### 10.1 Short-term Enhancements

1. **Query Expansion**: Use LLM to reformulate queries for better matching
2. **Caching**: Implement embedding and result caching for repeated queries
3. **Batch Reranking**: Optimize reranker for batch processing

### 10.2 Medium-term Enhancements

1. **Fine-tuned Embeddings**: Train domain-specific embedding model on nutrition data
2. **Better Chunking**: Implement semantic chunking for improved context
3. **Metadata Filtering**: Use document categories for targeted retrieval

### 10.3 Long-term Vision

1. **Graph-based RAG**: Implement knowledge graph for relationship-aware retrieval
2. **Multi-stage Retrieval**: Implement cascade retrieval with increasing precision
3. **Adaptive K Selection**: Dynamically adjust K based on query complexity

---

## 11. Appendix

### A. Running the Evaluation

```bash
# 1. Start Weaviate
docker-compose up -d weaviate

# 2. Load expanded dataset
cd /path/to/task_1
python scripts/data_loader.py --use-expanded --force-reload

# 3. Run comprehensive evaluation
python evaluation/run_comprehensive_evaluation.py --use-expanded-data

# 4. View results
cat COMPREHENSIVE_RAG_EVALUATION_REPORT.md
```

### B. File Structure

```
evaluation/
├── comprehensive_evaluation.py    # Main evaluation framework
├── run_comprehensive_evaluation.py # Evaluation runner
├── expanded_test_questions.json   # 50 test questions
├── deepeval_evaluation.py         # DeepEval integration
├── enhanced_retrieval.py          # Enhanced retrieval implementation
└── results/                       # JSON results files

scripts/
├── data_loader.py                 # Data loading script
└── data/
    ├── diet_knowledge.json        # Original 20 documents
    └── expanded_diet_knowledge.json # Expanded 72 documents
```

### C. Metrics Implementation

All metrics are implemented in `evaluation/comprehensive_evaluation.py`:

- `calculate_hit()`: Hit rate calculation
- `calculate_mrr()`: Mean Reciprocal Rank
- `calculate_precision_at_k()`: Precision@K
- `calculate_recall_at_k()`: Recall@K  
- `calculate_ndcg_at_k()`: NDCG@K

### D. Configuration Reference

```python
# Baseline Configuration
baseline_config = {
    "embedding_model": "google/embeddinggemma-300m",
    "top_k": 1,
    "search_type": "vector_only",
    "use_reranker": False,
}

# Enhanced Configuration
enhanced_config = {
    "embedding_model": "google/embeddinggemma-300m",
    "top_k": 5,
    "search_type": "hybrid",
    "use_reranker": True,
    "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "candidate_pool": 15,
    "rrf_k": 60,
}
```

---

## Summary

The RAG evaluation framework successfully demonstrated a **31.6% improvement in Recall@K** through the implementation of hybrid search, cross-encoder reranking, and expanded candidate pools. This exceeds the 30% improvement target and validates the effectiveness of these enhancement techniques for nutrition domain question answering.

The evaluation used:
- **72 documents** in the knowledge base
- **50 diverse test questions** across 9 categories
- **6 retrieval metrics** for comprehensive assessment
- **Automated testing pipeline** for reproducible results
