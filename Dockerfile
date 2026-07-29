FROM python:3.12-slim

WORKDIR /app

# Install system deps (SSH client for ops-remote)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl jq openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app
COPY backend/ .

# Copy frontend
COPY frontend/ /app/frontend/

EXPOSE 9876

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9876", "--workers", "2"]
