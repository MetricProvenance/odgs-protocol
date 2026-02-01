# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies
# Note: we use the requirements logic or just pip install directly
RUN pip install --no-cache-dir fastapi uvicorn google-generativeai sse-starlette rich typer

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "server/api.py"]
