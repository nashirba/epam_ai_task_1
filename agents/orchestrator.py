import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from mcp_servers.news_server import NewsMCPServer
from mcp_servers.weather_server import WeatherMCPServer
from settings.chat_model import init_chat_model

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """You are an intent detection assistant. Analyze the user's query and determine which services are needed.

Available intents:
- weather: Questions about weather conditions, temperature, forecasts, rain, etc.
- news: Questions about news, headlines, current events, articles
- both: Questions that require both weather AND news information
- general: General questions that don't require weather or news data

Respond with ONLY ONE of these words: weather, news, both, general

Examples:
- "What's the weather in London?" -> weather
- "Latest tech news" -> news
- "Weather in NYC and today's headlines" -> both
- "How are you?" -> general
"""


class AgentOrchestrator:
    def __init__(self, llm, weather_server: WeatherMCPServer, news_server: NewsMCPServer):
        self.llm = llm
        self.weather_server = weather_server
        self.news_server = news_server
        self._setup_tools()

    @classmethod
    async def create(cls):
        logger.info("Creating AgentOrchestrator")
        llm = init_chat_model()
        weather_server = WeatherMCPServer()
        news_server = NewsMCPServer()
        return cls(llm, weather_server, news_server)

    def _setup_tools(self):
        weather_server = self.weather_server
        news_server = self.news_server

        @tool
        async def get_weather(city: str) -> str:
            """Get current weather for a city."""
            return await weather_server.get_weather(city)

        @tool
        async def get_forecast(city: str, days: int = 3) -> str:
            """Get weather forecast for a city."""
            return await weather_server.get_forecast(city, days)

        @tool
        async def get_news(category: str = "general", limit: int = 5) -> str:
            """Get latest news headlines. Categories: general, technology, business, science, world"""
            return await news_server.get_news(category, limit)

        @tool
        async def search_news(query: str, limit: int = 5) -> str:
            """Search news by keyword."""
            return await news_server.search_news(query, limit)

        self.tools = [get_weather, get_forecast, get_news, search_news]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def detect_intent(self, query: str) -> str:
        logger.info(f"Detecting intent for query: {query}")

        messages = [SystemMessage(content=INTENT_SYSTEM_PROMPT), HumanMessage(content=query)]

        response = await self.llm.ainvoke(messages)
        intent = response.content.strip().lower()

        valid_intents = ["weather", "news", "both", "general"]
        if intent not in valid_intents:
            for valid in valid_intents:
                if valid in intent:
                    intent = valid
                    break
            else:
                intent = "general"

        logger.info(f"Detected intent: {intent}")
        return intent

    async def _extract_city(self, query: str) -> str:
        messages = [
            SystemMessage(
                content="Extract the city name from the query. Respond with ONLY the city name, nothing else. If no city is mentioned, respond with 'unknown'."
            ),
            HumanMessage(content=query),
        ]
        response = await self.llm.ainvoke(messages)
        city = response.content.strip()
        return city if city.lower() != "unknown" else None

    async def _extract_news_params(self, query: str) -> dict:
        messages = [
            SystemMessage(
                content="""Extract news parameters from the query.
Respond in this exact format:
category: <category>
search: <search term or none>

Categories: general, technology, business, science, world
If a specific topic is mentioned that's not a category, use it as search term.
"""
            ),
            HumanMessage(content=query),
        ]
        response = await self.llm.ainvoke(messages)

        params = {"category": "general", "search": None}
        for line in response.content.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                if key == "category" and value in ["general", "technology", "business", "science", "world"]:
                    params["category"] = value
                elif key == "search" and value.lower() != "none":
                    params["search"] = value

        return params

    async def process_query(self, query: str) -> dict[str, Any]:
        logger.info(f"Processing query: {query}")

        intent = await self.detect_intent(query)
        tools_used = []
        context_parts = []

        try:
            if intent == "weather":
                city = await self._extract_city(query)
                if city:
                    weather_data = await self.weather_server.get_weather(city)
                    context_parts.append(f"Weather data:\n{weather_data}")
                    tools_used.append(f"get_weather({city})")

                    if any(word in query.lower() for word in ["forecast", "tomorrow", "week", "days"]):
                        forecast_data = await self.weather_server.get_forecast(city)
                        context_parts.append(f"Forecast:\n{forecast_data}")
                        tools_used.append(f"get_forecast({city})")
                else:
                    context_parts.append("No city specified. Please provide a city name for weather information.")

            elif intent == "news":
                params = await self._extract_news_params(query)
                if params["search"]:
                    news_data = await self.news_server.search_news(params["search"])
                    context_parts.append(f"News search results for '{params['search']}':\n{news_data}")
                    tools_used.append(f"search_news({params['search']})")
                else:
                    news_data = await self.news_server.get_news(params["category"])
                    context_parts.append(f"Latest {params['category']} news:\n{news_data}")
                    tools_used.append(f"get_news({params['category']})")

            elif intent == "both":
                city = await self._extract_city(query)
                if city:
                    weather_data = await self.weather_server.get_weather(city)
                    context_parts.append(f"Weather in {city}:\n{weather_data}")
                    tools_used.append(f"get_weather({city})")

                params = await self._extract_news_params(query)
                if params["search"]:
                    news_data = await self.news_server.search_news(params["search"])
                    context_parts.append(f"News about '{params['search']}':\n{news_data}")
                    tools_used.append(f"search_news({params['search']})")
                else:
                    news_data = await self.news_server.get_news(params["category"])
                    context_parts.append(f"Latest news:\n{news_data}")
                    tools_used.append(f"get_news({params['category']})")

            context = "\n\n".join(context_parts) if context_parts else ""

            response_prompt = f"""You are a helpful assistant that provides weather and news information.

User query: {query}

{"Context from tools:" if context else ""}
{context}

Provide a helpful, concise response to the user's query based on the context above.
If no context is available, respond appropriately to the user's general question.
Format the response in a clear and readable way using markdown when appropriate.
"""

            messages = [HumanMessage(content=response_prompt)]
            response = await self.llm.ainvoke(messages)

            return {"answer": response.content, "intent": intent, "tools_used": tools_used}

        except Exception as e:
            logger.exception(f"Error processing query: {e}")
            return {
                "answer": f"I encountered an error while processing your request: {str(e)}. Please try again.",
                "intent": intent,
                "tools_used": tools_used,
                "error": str(e),
            }
