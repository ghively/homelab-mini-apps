FROM python:3.12-slim

WORKDIR /app

# Install system deps including 1Password CLI, SSH client
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl jq gnupg2 openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install 1Password CLI
RUN curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
    gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
    tee /etc/apt/sources.list.d/1password.list && \
    apt-get update && apt-get install -y --no-install-recommends 1password-cli && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app
COPY backend/ .

# Copy frontend
COPY frontend/ /app/frontend/

EXPOSE 9876

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9876", "--workers", "2"]
