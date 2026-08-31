# Use official slim Python runtime
FROM python:3.11-slim

# Install system dependencies (Git is required by GitPython)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .
COPY storage/ ./storage/
COPY agent/ ./agent/
COPY alerts/ ./alerts/
COPY data/ ./data/

# Expose default Cloud Run port
EXPOSE 8080

# Run FastAPI app with Uvicorn, binding to the dynamic PORT env var
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
