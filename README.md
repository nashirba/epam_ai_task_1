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
   git clone <repository-url>
   cd task_1
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
   
   Open your browser and navigate to: http://localhost:8501

## 📁 Project Structure

```
task_1/
├── app.py                 # Streamlit application
├── data_loader.py         # Script to load data into Weaviate
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Application container build
├── requirements.txt       # Python dependencies
├── PROJECT.md             # Detailed project documentation
├── README.md              # This file
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── data/
    └── diet_knowledge.json  # Diet & nutrition knowledge base
```

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `WEAVIATE_URL` | Weaviate database URL | `http://weaviate:8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

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
2. **Embedding**: Query is converted to a 1536-dimensional vector using OpenAI's text-embedding-ada-002
3. **Vector Search**: Weaviate finds the most similar documents using cosine similarity
4. **Context Building**: Top 3 relevant documents are formatted as context
5. **LLM Generation**: GPT-4o-mini generates a response using the query + context
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

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Weaviate**
   ```bash
   docker-compose up weaviate
   ```

3. **Load data**
   ```bash
   export OPENAI_API_KEY=your-key
   export WEAVIATE_URL=http://localhost:8080
   python data_loader.py
   ```

4. **Run Streamlit**
   ```bash
   streamlit run app.py
   ```

## ⚠️ Limitations

- Knowledge base is static and requires manual updates
- Responses depend on the quality and coverage of the dataset
- Not a substitute for professional medical or nutritional advice
- Rate limited by OpenAI API quotas
- Embedding model has token limits (8191 tokens per chunk)

## 📄 License

This project is for educational purposes.

---

**Note**: Always consult healthcare professionals for personalized dietary advice.
