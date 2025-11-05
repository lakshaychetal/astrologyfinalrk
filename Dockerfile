FROM python:3.10-slim

WORKDIR /app

# Copy and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config.py .
COPY astrology_rag.py .
COPY main.py .

# Expose port
EXPOSE 8080

# Cloud Run port environment variable
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080', timeout=5)"

# Run application
CMD ["python", "main.py"]
