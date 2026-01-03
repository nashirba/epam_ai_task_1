import asyncio
import logging
import sys
from datetime import datetime

import streamlit as st

from agents.orchestrator import AgentOrchestrator
from settings.logger import configure_logging

configure_logging()
logger = logging.getLogger("weather_news_agent")


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def main():
    logger.info("Starting Weather & News Agent Application")

    st.set_page_config(page_title="Weather & News Assistant", page_icon="🌤️", layout="wide")

    st.title("🌤️ Weather & News AI Assistant")
    st.markdown("""
    Welcome! I can help you with:
    - **Weather Information**: Current conditions, forecasts for any city
    - **Latest News**: Headlines from various categories and topics
    - **Combined Queries**: Ask about both weather and news in one question!
    """)
    st.divider()

    if "orchestrator" not in st.session_state:
        with st.spinner("Initializing AI Agent..."):
            try:
                loop = get_event_loop()
                st.session_state.orchestrator = loop.run_until_complete(AgentOrchestrator.create())
                logger.info("Agent orchestrator initialized successfully")
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
                logger.exception(f"Agent initialization failed: {e}")
                return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"🕐 {message['timestamp']}")

    if user_query := st.chat_input("Ask about weather or news..."):
        logger.info(f"User query received: {user_query}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({"role": "user", "content": user_query, "timestamp": timestamp})

        with st.chat_message("user"):
            st.markdown(user_query)
            st.caption(f"🕐 {timestamp}")

        with st.chat_message("assistant"):
            with st.spinner("Processing your request..."):
                try:
                    loop = get_event_loop()
                    response = loop.run_until_complete(st.session_state.orchestrator.process_query(user_query))

                    st.markdown(response["answer"])

                    if response.get("intent"):
                        st.caption(f"📊 Detected intent: {response['intent']}")

                    if response.get("tools_used"):
                        with st.expander("🔧 Tools Used"):
                            for tool in response["tools_used"]:
                                st.markdown(f"- {tool}")

                    response_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"🕐 {response_timestamp}")

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response["answer"],
                            "timestamp": response_timestamp,
                            "intent": response.get("intent"),
                            "tools_used": response.get("tools_used"),
                        }
                    )

                    logger.info("Response generated successfully")

                except Exception as e:
                    error_msg = f"Error processing request: {e}"
                    st.error(error_msg)
                    logger.exception(error_msg)

    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant uses **Agent Orchestration** with **MCP**
        (Model Context Protocol) to provide real-time weather and news information.
        """)

        st.divider()
        st.header("💡 Example Questions")
        st.markdown("""
        **Weather:**
        - What's the weather in London?
        - Will it rain tomorrow in Paris?
        - Current temperature in Tokyo?

        **News:**
        - What are the latest headlines?
        - News about technology
        - Recent business news

        **Combined:**
        - Weather in NYC and tech news
        - What's happening in the world today?
        """)

        st.divider()
        st.header("🔄 Actions")
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
