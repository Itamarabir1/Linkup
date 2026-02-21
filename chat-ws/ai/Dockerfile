# Dockerfile for Python AI Analyzer service
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the service
CMD ["python", "-m", "service.chat_analyzer_service"]
