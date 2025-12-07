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
import sys

import weaviate
from langchain_openai import AzureOpenAIEmbeddings
from weaviate.util import generate_uuid5

from settings import configs
from settings.db import create_schema, init_weaviate_client
from settings.embedding import init_embedding
from settings.logger import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger("data_loader")


def get_data_with_embedding_vector(embedding_model: AzureOpenAIEmbeddings) -> list[dict]:
    logger.info(f"Loading data from {configs.DATA_FILE}")
    with open(configs.DATA_FILE) as f:
        documents_data = json.load(f)

    logger.info(f"Found {len(documents_data)} documents to process")

    logger.info("Generating embeddings for all documents")
    contents_to_embed = [doc["content"] for doc in documents_data]
    vector_embeddings = embedding_model.embed_documents(contents_to_embed)
    if isinstance(vector_embeddings, dict):
        # If API returns a dict instead of list, that means an error (e.g. model is still loading)
        raise ValueError(f"HuggingFace API Error assumed: {vector_embeddings}")

    logger.info(f"Generated {len(vector_embeddings)} embeddings. Vector dimension: {len(vector_embeddings[0])}")

    for i, doc in enumerate(documents_data):
        doc["content_vector"] = vector_embeddings[i]

    return documents_data


def load_data(collection: weaviate.collections.Collection, documents_data: list[dict]) -> None:
    logger.info(f"Ingesting {len(documents_data)} documents into database")

    # Use a context manager to automatically handle batching
    with collection.batch.dynamic() as batch:
        for doc in documents_data:
            properties = {
                "doc_id": doc["id"],
                "category": doc["category"],
                "title": doc["title"],
                "content": doc["content"],
            }
            batch.add_object(
                properties=properties,
                vector=doc["content_vector"],  # Use default vector
                uuid=generate_uuid5(doc["title"]),  # Generate a consistent UUID based on the title
            )

    logger.info(f"Data ingestion complete. Total objects in collection: {len(collection)}")


def verify_data(collection: weaviate.collections.Collection) -> None:
    """Verify the loaded data."""
    logger.info("Verifying loaded data...")

    count = collection.aggregate.over_all(total_count=True).total_count
    logger.info(f"Total documents in collection: {count}")

    sample = collection.query.fetch_objects(limit=1)
    if sample.objects:
        logger.info(f"Sample document title: {sample.objects[0].properties['title']}")


def main():
    logger.info("=" * 60)
    logger.info("Starting Diet & Nutrition RAG Data Loader")
    logger.info("=" * 60)

    if configs.SKIP_DATA_LOADER:
        logger.info("Skipping data loader due to SKIP_DATA_LOADER environment variable")
        return

    if not configs.AZURE_OPENAI_API_KEY:
        logger.error("AZURE_OPENAI_API_KEY environment variable is not set!")
        sys.exit(1)
    logger.info("OpenAI API key found")

    if not configs.DATA_FILE.exists():
        logger.error(f"Data file not found: {configs.DATA_FILE}")
        sys.exit(1)
    logger.info(f"Data file found: {configs.DATA_FILE}")

    weaviate_client = None
    try:
        weaviate_client = init_weaviate_client(configs.WEAVIATE_URL)

        embedding_model = init_embedding()
        logger.info("Embedding model initialized")

        rag_collection = create_schema(weaviate_client, configs.COLLECTION_NAME)
        documents_data = get_data_with_embedding_vector(embedding_model)
        load_data(rag_collection, documents_data)

        verify_data(rag_collection)

        logger.info("=" * 60)
        logger.info("Data loading completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Error during data loading: {e}")
        sys.exit(1)
    finally:
        if weaviate_client:
            weaviate_client.close()


if __name__ == "__main__":
    main()
