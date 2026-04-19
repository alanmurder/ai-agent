# Main Agent Core Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir hatch \
    && hatch build \
    && pip install --no-cache-dir dist/*.whl

# Copy application code
COPY core/ ./core/
COPY skills/ ./skills/
COPY gateway/ ./gateway/
COPY storage/ ./storage/
COPY config/ ./config/

# Create data directories
RUN mkdir -p /data /logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEPLOY_MODE=docker

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:18789/health || exit 1

# Run the agent
EXPOSE 18789
CMD ["python", "-m", "core.agent.engine"]