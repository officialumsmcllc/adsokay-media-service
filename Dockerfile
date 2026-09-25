FROM python:3.11-slim

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Persistent storage mount point
ENV STORAGE_DIR=/var/data/images
RUN mkdir -p /var/data/images

EXPOSE 8000

CMD ["./start.sh"]
