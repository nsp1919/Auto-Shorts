FROM python:3.10

# Install system dependencies
# Added ca-certificates and curl/wget for robust networking
# Added iputils-ping and dnsutils for debugging
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    ca-certificates \
    curl \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Run as root (default) to fix permissions issues in HF Spaces
# Removed user creation and switching

# Working directory
WORKDIR /app

# Copy requirements (adjusting path if needed, assuming backend/requirements.txt exists)
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create directories
RUN mkdir -p uploads processed && \
    chmod 777 uploads processed

# Expose port
EXPOSE 7860

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
