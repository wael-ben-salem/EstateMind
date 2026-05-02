FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY price_predictor.py anomaly_detector.py price_service.py anomaly_service.py ./

# Default port (overridden by docker-compose command)
EXPOSE 8001

CMD ["uvicorn", "price_service:app", "--host", "0.0.0.0", "--port", "8001"]
