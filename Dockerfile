FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY README.md ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Create necessary directories
RUN mkdir -p data/logs data/cache data/user_data

# Set the default command
CMD ["poetry", "run", "python", "-m", "src.secondbrain.main"] 