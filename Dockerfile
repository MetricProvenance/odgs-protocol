FROM python:3.11-slim

WORKDIR /app

# System deps for git operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY lib/ lib/
COPY specifications/ specifications/
COPY .streamlit/ .streamlit/

# Install the package
RUN pip install --no-cache-dir .

# Initialize a git repo so GitPython can work
RUN git config --global user.email "odgs@metricprovenance.com" && \
    git config --global user.name "ODGS Demo" && \
    git init && git add -A && git commit -m "init" --allow-empty

# Streamlit config for Docker
RUN mkdir -p /root/.streamlit && \
    echo '[server]' > /root/.streamlit/config.toml && \
    echo 'headless = true' >> /root/.streamlit/config.toml && \
    echo 'port = 8501' >> /root/.streamlit/config.toml && \
    echo 'address = "0.0.0.0"' >> /root/.streamlit/config.toml && \
    echo 'enableCORS = false' >> /root/.streamlit/config.toml && \
    echo 'enableXsrfProtection = false' >> /root/.streamlit/config.toml

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/odgs/ui/dashboard.py"]
