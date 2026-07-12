FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Remotion + Hyperframes)
RUN # REMOVED BY REPOGUARD: curl|bash remote execution - \
    && apt-get install -y nodejs

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default environment
ENV PYTHONUNBUFFERED=1

# Expose port for API (if needed)
EXPOSE 8080

# Default command: run the CLI
ENTRYPOINT ["python", "-m", "orchestrator.main"]
CMD ["status"]
