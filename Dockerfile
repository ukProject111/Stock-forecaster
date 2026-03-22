FROM python:3.11-slim

WORKDIR /app

# Install system deps for curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
# Copy models and data (needed for predictions)
COPY models/ ./models/
COPY data/ ./data/

WORKDIR /app/backend

ENV PORT=10000
EXPOSE 10000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
