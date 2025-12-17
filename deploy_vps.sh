#!/bin/bash

# Auto-Shorts Downloader VPS Deployment Script
# Usage: ./deploy_vps.sh

echo "🚀 Starting Deployment..."

# 1. Update System
echo "📦 Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker if not exists
if ! command -v docker &> /dev/null
then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️  Docker installed. You might need to log out and log back in for group changes to take effect."
else
    echo "✅ Docker is already installed"
fi

# 3. Clone/Pull Repo (Assumes script is run inside the repo or you clone it)
# Ideally, user clones repo then runs this.
echo "📂 Building Container..."
# Navigate to downloader directory
cd yt-downloader || { echo "❌ yt-downloader directory not found!"; exit 1; }

# 4. Build Docker Image
sudo docker build -t yt-downloader .

# 5. Stop existing container if running
echo "🛑 Stopping old container..."
sudo docker stop yt-downloader-service 2>/dev/null || true
sudo docker rm yt-downloader-service 2>/dev/null || true

# 6. Run New Container
echo "▶️  Starting new container..."
# Run on port 8000, restart always
sudo docker run -d \
  --name yt-downloader-service \
  --restart always \
  -p 8000:8000 \
  yt-downloader

echo "✅ Deployment Complete!"
echo "🌍 Service running on port 8000."
echo "   Test URL: http://$(curl -s ifconfig.me):8000/"
