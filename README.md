# Weather & News MCP Agent

An AI-powered application that answers questions about current weather conditions and latest news using **Agent Orchestration** patterns and **MCP (Model Context Protocol)** for standardized tool integration.

## Features

- **Weather Information**: Real-time weather data and forecasts using Open-Meteo API
- **News Headlines**: Latest news from multiple RSS feeds across various categories
- **Agent Orchestration**: LLM-based intent detection to route queries appropriately
- **MCP Integration**: Standardized tool protocol for weather and news services
- **Multi-turn Conversations**: Chat-like interface with conversation history
- **No API Keys Required**: Weather (Open-Meteo) and News (RSS feeds) work without API keys

## Architecture

```
Streamlit UI (User Input)
       |
       |
       ▼
Agent Orchestrator (LLM + Intent Detection)
       |                    |
       |                    |
       ▼                    ▼
LLM Provider           MCP Servers
(Groq/xAI/OpenR)       Weather (Open-Meteo) and News (RSS Feeds)
```

### Components

1. **Streamlit UI** (`app.py`): Web interface for user interactions
2. **Agent Orchestrator** (`agents/orchestrator.py`): 
   - LLM-based intent detection (weather, news, both, general)
   - Query routing to appropriate MCP servers
   - Response aggregation and formatting
3. **MCP Servers** (`mcp_servers/`):
   - **Weather Server**: Open-Meteo API integration (no API key)
   - **News Server**: RSS feed aggregation (no API key)

## Quick Start

### Prerequisites

- Python 3.10+
- One of the following LLM API keys:
  - **Groq** (recommended, free tier): [console.groq.com](https://console.groq.com/)
  - **xAI Grok**: [console.x.ai](https://console.x.ai/)
  - **OpenRouter** (free models available): [openrouter.ai](https://openrouter.ai/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nashirba/epam_ai_task_1/tree/feature/module_5
   cd task_1
   ```

2. **Create virtual environment**
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # or .venv\Scripts\activate  # Windows
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API key
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   Navigate to: http://localhost:8501

## Project Structure

```
project/
├── app.py                    # Main Streamlit application
├── agents/
│   ├── __init__.py
│   └── orchestrator.py       # Agent orchestration with LLM intent detection
├── mcp_servers/
│   ├── __init__.py
│   ├── weather_server.py     # Weather MCP server (Open-Meteo)
│   └── news_server.py        # News MCP server (RSS feeds)
├── mcp_config/
│   └── mcp_servers.json      # MCP server configuration
├── settings/
│   ├── __init__.py
│   ├── configs.py            # Application configuration
│   ├── chat_model.py         # LLM initialization
│   └── logger.py             # Logging configuration
├── pyproject.toml            # Project dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## Configuration

### LLM Providers

The application supports multiple LLM providers. Set `LLM_PROVIDER` in `.env`:

| Provider | Environment Variable | Free Tier |
|----------|---------------------|---------|
| Groq | `GROQ_API_KEY` | Yes (recommended) |
| xAI Grok | `XAI_API_KEY` | Limited |
| OpenRouter | `OPENROUTER_API_KEY` | Free models available |

### News RSS Feeds

News sources are configured in `settings/configs.py`:
- **General**: BBC News, CNN
- **Technology**: TechCrunch, Ars Technica
- **Business**: BBC Business, CNBC
- **Science**: BBC Science, ScienceDaily
- **World**: BBC World, NY Times

## Example Queries

### Weather
- "What's the weather in London?"
- "Will it rain tomorrow in Paris?"
- "Show me the 5-day forecast for Tokyo"

### News
- "What are the latest headlines?"
- "Technology news today"
- "News about artificial intelligence"

### Combined
- "Weather in NYC and tech news"
- "What's happening in the world today?"

## How It Works

### Intent Detection

The agent uses an LLM to classify user queries into intents:
- `weather`: Weather-related queries
- `news`: News-related queries  
- `both`: Queries requiring both weather and news
- `general`: General conversation

### MCP Integration

MCP (Model Context Protocol) provides a standardized way to integrate external tools:

1. **Weather MCP Server** (`mcp_servers/weather_server.py`):
   - Uses Open-Meteo free API
   - Provides current weather and forecasts
   - Includes geocoding for city name lookup

2. **News MCP Server** (`mcp_servers/news_server.py`):
   - Aggregates multiple RSS feeds
   - Supports category filtering
   - Includes keyword search


## Assumptions & Limitations

- Weather data is provided by Open-Meteo (free, no API key required)
- News data is sourced from public RSS feeds (no API key required)
- LLM API key is required for intent detection and response generation
- RSS feeds may have rate limits or temporary unavailability
- Weather forecasts are limited to 7 days maximum

## Data Sources

### Weather
- **Open-Meteo API**: [open-meteo.com](https://open-meteo.com/)
  - Free, open-source weather API
  - No API key required
  - Global coverage

### News (RSS Feeds)
- BBC News
- CNN
- TechCrunch
- Ars Technica
- CNBC
- ScienceDaily
- NY Times
