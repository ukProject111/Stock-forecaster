FROM python:3.11-slim

WORKDIR /app

# Install deps with no cache to save memory
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
# Copy models and data (needed for predictions)
COPY models/ ./models/
COPY data/ ./data/

WORKDIR /app/backend

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
