FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Setup user for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Working directory
WORKDIR $HOME/app

# Copy requirements
COPY --chown=user backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY --chown=user backend/ .

# Create directories
RUN mkdir -p uploads processed && \
    chmod 777 uploads processed

# Expose port
EXPOSE 7860

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
