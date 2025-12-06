# Diet & Nutrition RAG Assistant

## Main Idea
An AI-powered Diet and Nutrition Assistant that provides personalized dietary advice, meal planning suggestions, and nutritional information based on a curated knowledge base of diet and nutrition data. The system uses RAG (Retrieval-Augmented Generation) to enhance LLM responses with accurate, domain-specific information.

## Concepts
- **RAG (Retrieval-Augmented Generation)**: Combines information retrieval with generative AI to provide accurate, contextual responses
- **Vector Embeddings**: Converts text chunks into numerical vectors for semantic similarity search
- **Semantic Search**: Finds relevant information based on meaning rather than exact keyword matching
- **Context Window Enhancement**: Augments LLM prompts with retrieved relevant documents

## Design Details

### Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  RAG Application │────▶│   Weaviate DB   │
│  (User Input)   │     │   (Python App)   │     │ (Vector Search) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌──────────────────┐
                        │   OpenAI API     │
                        │ (LLM + Embeddings)│
                        └──────────────────┘
```

### Data Flow
1. User submits a diet/nutrition question via Streamlit UI
2. Question is converted to embedding vector using OpenAI's embedding model
3. Weaviate performs vector similarity search to find relevant documents
4. Retrieved documents + original question are sent to LLM
5. LLM generates contextual response displayed to user

## Dataset Concept
The dataset consists of curated diet and nutrition information organized into categories:
- **Macronutrients**: Information about proteins, carbohydrates, and fats
- **Micronutrients**: Vitamins and minerals essential for health
- **Diet Types**: Mediterranean, Keto, Vegan, Paleo, etc.
- **Meal Planning**: Guidance for balanced meal composition
- **Special Diets**: Diabetic, heart-healthy, weight loss diets
- **Food Facts**: Nutritional information about common foods

## System Technical Details

### Technology Stack
- **Vector Database**: Weaviate (open-source, Docker-based)
- **Embedding Model**: OpenAI text-embedding-ada-002 (1536 dimensions)
- **LLM**: OpenAI GPT-4o-mini (via API)
- **UI Framework**: Python Streamlit
- **Container Orchestration**: Docker Compose
- **Programming Language**: Python 3.11

### Components
1. **docker-compose.yml**: Orchestrates Weaviate and application containers
2. **data_loader.py**: Script to create embeddings and populate Weaviate
3. **app.py**: Streamlit application with RAG implementation
4. **data/**: Directory containing diet and nutrition knowledge base

## Requirements
- Docker and Docker Compose
- OpenAI API key
- Python 3.11+
- Internet connection for API calls

## Limitations
- Responses depend on the quality and coverage of the knowledge base
- Not a substitute for professional medical or nutritional advice
- Rate limited by OpenAI API quotas
- Embedding model has token limits per chunk (8191 tokens for ada-002)
- Knowledge base is static and requires manual updates
