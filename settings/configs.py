import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DATA_FILE = Path(__file__).parent.parent / "scripts" / "data" / "diet_knowledge.json"
COLLECTION_NAME = "DietKnowledge"
EMBEDDING_MODEL = "text-embedding-ada-002"
TOP_K_RESULTS = 3

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "YOUR_AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "YOUR_EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "YOUR_CHAT_DEPLOYMENT_NAME")
