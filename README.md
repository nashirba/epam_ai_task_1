# 🥗 Diet & Nutrition RAG Assistant

A Retrieval-Augmented Generation (RAG) application for diet and nutrition information, built with Python, Streamlit, Weaviate, and OpenAI.

## 📋 Features

- **Semantic Search**: Vector-based similarity search for relevant nutrition information
- **RAG Pipeline**: Combines retrieval with LLM generation for accurate, contextual responses
- **Interactive UI**: User-friendly Streamlit interface with chat history
- **Comprehensive Logging**: All operations logged for container visibility
- **Docker Compose**: Easy deployment with containerized services

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nashirba/epam_ai_task_1.git
   cd task_1
   git branch RAG_assignment_1
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   
   Open your browser and navigate to: http://localhost:8000


## 📊 Dataset

The knowledge base includes 20 curated documents covering:

- **Macronutrients**: Proteins, Carbohydrates, Fats
- **Micronutrients**: Vitamin D, Vitamin B12, Iron
- **Diet Types**: Mediterranean, Keto, Vegan, Paleo
- **Meal Planning**: Balanced composition, Timing
- **Special Diets**: Weight loss, Diabetic, Heart-healthy
- **Food Facts**: Eggs, Salmon, Spinach
- **Nutrition Basics**: Hydration, Supplements

## 🔍 How RAG Works

1. **User Query**: User asks a diet/nutrition question
2. **Embedding**: Query is converted to a 768-dimensional vector using local embedding model
3. **Vector Search**: Weaviate finds the most similar documents using cosine similarity
4. **Context Building**: Top 5 relevant documents are formatted as context
5. **LLM Generation**: HuggingFace LLM model generates a response using the query + context
6. **Response Display**: Answer is shown with source documents

## 📝 Viewing Logs

All operations are logged to stdout for container visibility:

```bash
# View all logs
docker-compose logs -f

# View only application logs
docker-compose logs -f diet-rag-app

# View only Weaviate logs
docker-compose logs -f weaviate
```

## 🛠️ Development

### Local Development (without Docker)

1. **Install uv**

Using official installation:
```bash
# На macOS и Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or using pip:
```bash
pip install uv
```

2. **Install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # На Linux/macOS
   # или .venv\Scripts\activate на Windows
   uv sync
   ```

3. **Fill .env file using .env.example**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Start Weaviate**
   ```bash
   docker-compose up weaviate
   ```

5. **Load data**
   ```bash
   python data_loader.py
   ```

6**Run Streamlit**
   ```bash
   streamlit run app.py
   ```

**Note**: Always consult healthcare professionals for personalized dietary advice.
