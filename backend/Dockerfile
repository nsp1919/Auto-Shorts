FROM python:3.10-slim

# Install system dependencies (FFmpeg is critical)
# Added iputils-ping and dnsutils for debugging network
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Running as root (default) to avoid permission-based network issues in some environments

# Set working directory
WORKDIR /app

# Copy requirement.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads processed && \
    chmod 777 uploads processed

# Expose the port that Hugging Face Spaces expects (7860)
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
