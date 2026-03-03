FROM python:3.11-slim

WORKDIR /app

# System deps for git operations and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY 2_INFORMATIVE_REFERENCE/ 2_INFORMATIVE_REFERENCE/
COPY 1_NORMATIVE_SPECIFICATION/ 1_NORMATIVE_SPECIFICATION/
COPY .streamlit/ .streamlit/

# Install the package with all optional dependencies including 'demo' (streamlit)
RUN pip install --no-cache-dir .[all]

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

CMD ["streamlit", "run", "2_INFORMATIVE_REFERENCE/src/odgs/ui/dashboard.py"]
