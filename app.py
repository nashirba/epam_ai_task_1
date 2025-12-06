#!/usr/bin/env python3
"""
Diet & Nutrition RAG Assistant - Streamlit Application

This application provides an AI-powered diet and nutrition assistant
using RAG (Retrieval-Augmented Generation) with Weaviate and OpenAI.

All operations are logged for container visibility.
"""

import logging
import os
import sys
import time

import streamlit as st
import weaviate
from weaviate.classes.query import MetadataQuery
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("diet_rag_app")

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "DietKnowledge"
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-4o-mini"
TOP_K_RESULTS = 3


def init_weaviate_client() -> weaviate.WeaviateClient:
    """Initialize Weaviate client with connection retry."""
    logger.info(f"Initializing Weaviate client connection to {WEAVIATE_URL}")
    
    max_retries = 10
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
                logger.info("Weaviate client connected successfully")
                return client
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: {e}")
            time.sleep(2)
    
    raise ConnectionError("Could not connect to Weaviate")


def init_openai_client() -> OpenAI:
    """Initialize OpenAI client."""
    logger.info("Initializing OpenAI client")
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_embedding(openai_client: OpenAI, text: str) -> list[float]:
    """Generate embedding vector for query text."""
    logger.info(f"Generating embedding for query: {text[:50]}...")
    
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    
    embedding = response.data[0].embedding
    logger.info(f"Generated embedding with {len(embedding)} dimensions")
    return embedding


def search_similar_documents(
    weaviate_client: weaviate.WeaviateClient,
    query_vector: list[float],
    top_k: int = TOP_K_RESULTS
) -> list[dict]:
    """Search for similar documents in Weaviate."""
    logger.info(f"Searching for top {top_k} similar documents")
    
    collection = weaviate_client.collections.get(COLLECTION_NAME)
    
    results = collection.query.near_vector(
        near_vector=query_vector,
        limit=top_k,
        return_metadata=MetadataQuery(distance=True)
    )
    
    documents = []
    for obj in results.objects:
        doc = {
            "title": obj.properties["title"],
            "category": obj.properties["category"],
            "content": obj.properties["content"],
            "distance": obj.metadata.distance if obj.metadata else None
        }
        documents.append(doc)
        logger.info(f"  - Found: {doc['title']} (distance: {doc['distance']:.4f})")
    
    logger.info(f"Retrieved {len(documents)} relevant documents")
    return documents


def format_context(documents: list[dict]) -> str:
    """Format retrieved documents as context for LLM."""
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[Document {i}: {doc['title']} ({doc['category']})]\n{doc['content']}"
        )
    return "\n\n".join(context_parts)


def generate_response(
    openai_client: OpenAI,
    user_query: str,
    context: str
) -> str:
    """Generate LLM response using RAG context."""
    logger.info("Generating LLM response with RAG context")
    
    system_prompt = """You are a helpful Diet and Nutrition Assistant. 
You provide accurate, evidence-based information about diet, nutrition, and healthy eating.
Use the provided context documents to answer questions accurately.
If the context doesn't contain relevant information, say so and provide general guidance.
Always encourage consulting with healthcare professionals for personalized advice.
Be friendly, clear, and supportive in your responses."""
    
    user_prompt = f"""Based on the following context documents, please answer the user's question.

CONTEXT:
{context}

USER QUESTION:
{user_query}

Please provide a helpful and accurate response based on the context above."""
    
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    answer = response.choices[0].message.content
    logger.info(f"Generated response ({len(answer)} characters)")
    return answer


def main():
    """Main Streamlit application."""
    logger.info("Starting Diet & Nutrition RAG Application")
    
    # Page configuration
    st.set_page_config(
        page_title="Diet & Nutrition Assistant",
        page_icon="🥗",
        layout="wide"
    )
    
    # Title and description
    st.title("🥗 Diet & Nutrition RAG Assistant")
    st.markdown("""
    Welcome to the Diet & Nutrition Assistant! Ask me anything about:
    - **Macronutrients** (proteins, carbs, fats)
    - **Micronutrients** (vitamins, minerals)
    - **Diet Types** (Mediterranean, Keto, Vegan, Paleo)
    - **Meal Planning** tips and strategies
    - **Special Diets** (weight loss, diabetic, heart-healthy)
    - **Food Facts** and nutritional information
    """)
    
    st.divider()
    
    # Initialize clients (cached)
    if "weaviate_client" not in st.session_state:
        with st.spinner("Connecting to database..."):
            try:
                st.session_state.weaviate_client = init_weaviate_client()
                logger.info("Weaviate client stored in session state")
            except Exception as e:
                st.error(f"Failed to connect to database: {e}")
                logger.error(f"Weaviate connection failed: {e}")
                return
    
    if "openai_client" not in st.session_state:
        if not OPENAI_API_KEY:
            st.error("OpenAI API key not configured!")
            logger.error("OPENAI_API_KEY not set")
            return
        st.session_state.openai_client = init_openai_client()
        logger.info("OpenAI client stored in session state")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 View Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['title']}** ({source['category']})")
                        st.caption(source['content'][:200] + "...")
    
    # User input
    if user_query := st.chat_input("Ask me about diet and nutrition..."):
        logger.info(f"User query received: {user_query}")
        
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    # Step 1: Generate embedding for query
                    query_vector = generate_embedding(
                        st.session_state.openai_client,
                        user_query
                    )
                    
                    # Step 2: Search for relevant documents
                    documents = search_similar_documents(
                        st.session_state.weaviate_client,
                        query_vector
                    )
                    
                    # Step 3: Format context
                    context = format_context(documents)
                    logger.info(f"Context prepared ({len(context)} characters)")
                    
                    # Step 4: Generate LLM response
                    response = generate_response(
                        st.session_state.openai_client,
                        user_query,
                        context
                    )
                    
                    # Display response
                    st.markdown(response)
                    
                    # Display sources
                    if documents:
                        with st.expander("📚 View Sources"):
                            for doc in documents:
                                st.markdown(f"**{doc['title']}** ({doc['category']})")
                                st.caption(f"Relevance: {1 - doc['distance']:.2%}")
                                st.caption(doc['content'][:200] + "...")
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": documents
                    })
                    
                    logger.info("Response generated and displayed successfully")
                    
                except Exception as e:
                    error_msg = f"Error generating response: {e}"
                    st.error(error_msg)
                    logger.exception(error_msg)
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant uses **RAG (Retrieval-Augmented Generation)** 
        to provide accurate diet and nutrition information.
        
        **How it works:**
        1. Your question is converted to a vector embedding
        2. Similar documents are retrieved from the knowledge base
        3. The LLM generates a response using the retrieved context
        """)
        
        st.divider()
        st.header("💡 Example Questions")
        st.markdown("""
        - What are the benefits of the Mediterranean diet?
        - How much protein do I need daily?
        - What foods are high in vitamin D?
        - Is the keto diet safe for everyone?
        - What should a balanced meal look like?
        """)
        
        st.divider()
        st.caption("⚠️ This is for educational purposes only. Consult a healthcare professional for personalized advice.")


if __name__ == "__main__":
    main()
