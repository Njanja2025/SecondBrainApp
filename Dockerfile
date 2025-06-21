FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
<<<<<<< HEAD
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false
=======
    PYTHONUNBUFFERED=1
>>>>>>> 46133858 (Initial auto-push with Visco: Docker, Compose, Makefile, README)

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
<<<<<<< HEAD
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
=======
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

# Default command (update this to your main app)
CMD ["streamlit", "run", "streamlit_app/main.py"]
>>>>>>> 46133858 (Initial auto-push with Visco: Docker, Compose, Makefile, README)
