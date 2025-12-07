FROM python:3.13.3-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LOG_LEVEL=INFO

# Install git (needed for git-based dependencies)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock /tmp/

# Install dependencies using uv
WORKDIR /tmp
RUN uv sync --frozen --no-dev

WORKDIR /app

# Ensure the virtual environment is in PATH
ENV PATH="/tmp/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Copy application code
COPY . .

# Run the application
CMD ["sh", "-c", "python scripts/data_loader.py && streamlit run app.py --server.address=0.0.0.0 --server.port=8000"]
