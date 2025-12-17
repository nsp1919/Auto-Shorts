FROM python:3.10-slim

# Install system dependencies (FFmpeg is critical)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy requirement.txt first to leverage Docker cache
COPY --chown=user requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . .

# Create necessary directories with permissions
RUN mkdir -p uploads processed && \
    chmod 777 uploads processed

# Expose the port that Hugging Face Spaces expects (7860)
EXPOSE 7860

# Command to run the application
# Use 0.0.0.0 for host to be accessible externally
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
