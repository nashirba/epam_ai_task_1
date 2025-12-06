#!/usr/bin/env python3
"""
Data Loader Script for Diet & Nutrition RAG System

This script:
1. Connects to Weaviate vector database
2. Creates the schema for diet knowledge
3. Generates embeddings using OpenAI
4. Loads all diet knowledge into Weaviate

All steps are logged for visibility in container logs.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/logs/data_loader.log") if os.path.exists("/app/logs") else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("data_loader")

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_FILE = Path(__file__).parent / "data" / "diet_knowledge.json"
COLLECTION_NAME = "DietKnowledge"
EMBEDDING_MODEL = "text-embedding-ada-002"


def wait_for_weaviate(max_retries: int = 30, delay: int = 2) -> weaviate.WeaviateClient:
    """Wait for Weaviate to be ready and return client."""
    logger.info(f"Connecting to Weaviate at {WEAVIATE_URL}")
    
    for attempt in range(max_retries):
        try:
            client = weaviate.connect_to_custom(
                http_host=WEAVIATE_URL.replace("http://", "").split(":")[0],
                http_port=int(WEAVIATE_URL.split(":")[-1]),
                http_secure=False,
                grpc_host=WEAVIATE_URL.replace("http://", "").split(":")[0],
                grpc_port=50051,
                grpc_secure=False,
            )
            if client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return client
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Weaviate not ready - {e}")
        
        time.sleep(delay)
    
    raise ConnectionError(f"Could not connect to Weaviate after {max_retries} attempts")


def create_schema(client: weaviate.WeaviateClient) -> None:
    """Create the Weaviate collection schema."""
    logger.info(f"Creating collection schema: {COLLECTION_NAME}")
    
    # Check if collection already exists
    if client.collections.exists(COLLECTION_NAME):
        logger.info(f"Collection {COLLECTION_NAME} already exists, checking data...")
        collection = client.collections.get(COLLECTION_NAME)
        count = collection.aggregate.over_all(total_count=True).total_count
        if count > 0:
            logger.info(f"Collection already has {count} objects. Skipping data load.")
            return True
        else:
            logger.info("Collection exists but is empty. Will load data.")
            return False
    
    # Create new collection
    client.collections.create(
        name=COLLECTION_NAME,
        properties=[
            Property(name="doc_id", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
        ],
        vectorizer_config=Configure.Vectorizer.none(),
    )
    
    logger.info(f"Collection {COLLECTION_NAME} created successfully")
    return False


def generate_embedding(openai_client: OpenAI, text: str) -> list[float]:
    """Generate embedding vector for text using OpenAI."""
    logger.debug(f"Generating embedding for text: {text[:50]}...")
    
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    
    return response.data[0].embedding


def load_data(client: weaviate.WeaviateClient, openai_client: OpenAI) -> None:
    """Load diet knowledge data into Weaviate."""
    logger.info(f"Loading data from {DATA_FILE}")
    
    # Load JSON data
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    
    logger.info(f"Found {len(data)} documents to process")
    
    # Get collection
    collection = client.collections.get(COLLECTION_NAME)
    
    # Process and insert each document
    for i, doc in enumerate(data):
        logger.info(f"Processing document {i + 1}/{len(data)}: {doc['title']}")
        
        # Create text for embedding (title + content)
        embedding_text = f"{doc['title']}: {doc['content']}"
        
        # Generate embedding
        vector = generate_embedding(openai_client, embedding_text)
        logger.info(f"  - Generated embedding with {len(vector)} dimensions")
        
        # Insert into Weaviate
        collection.data.insert(
            properties={
                "doc_id": doc["id"],
                "category": doc["category"],
                "title": doc["title"],
                "content": doc["content"],
            },
            vector=vector
        )
        logger.info(f"  - Inserted document into Weaviate")
    
    logger.info(f"Successfully loaded {len(data)} documents into Weaviate")


def verify_data(client: weaviate.WeaviateClient) -> None:
    """Verify the loaded data."""
    logger.info("Verifying loaded data...")
    
    collection = client.collections.get(COLLECTION_NAME)
    count = collection.aggregate.over_all(total_count=True).total_count
    
    logger.info(f"Total documents in collection: {count}")
    
    # Sample query to verify
    sample = collection.query.fetch_objects(limit=1)
    if sample.objects:
        logger.info(f"Sample document title: {sample.objects[0].properties['title']}")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Starting Diet & Nutrition RAG Data Loader")
    logger.info("=" * 60)
    
    # Validate OpenAI API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        sys.exit(1)
    logger.info("OpenAI API key found")
    
    # Check if data file exists
    if not DATA_FILE.exists():
        logger.error(f"Data file not found: {DATA_FILE}")
        sys.exit(1)
    logger.info(f"Data file found: {DATA_FILE}")
    
    try:
        # Connect to Weaviate
        weaviate_client = wait_for_weaviate()
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
        
        # Create schema
        data_exists = create_schema(weaviate_client)
        
        if not data_exists:
            # Load data only if collection is empty
            load_data(weaviate_client, openai_client)
        
        # Verify data
        verify_data(weaviate_client)
        
        logger.info("=" * 60)
        logger.info("Data loading completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"Error during data loading: {e}")
        sys.exit(1)
    finally:
        if 'weaviate_client' in locals():
            weaviate_client.close()


if __name__ == "__main__":
    main()
