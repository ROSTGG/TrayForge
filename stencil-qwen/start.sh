#!/bin/bash
# Quick start script for Gerber Stencil Generator Web Application

set -e

echo "🚀 Starting Gerber Stencil Generator..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        echo "❌ Docker Compose is not installed. Please install Docker Compose v2 or docker-compose first."
        exit 1
    fi
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Build and start
echo "📦 Building Docker images (this may take a few minutes on first run)..."
$COMPOSE_CMD up --build -d

echo ""
echo "✅ Application is ready!"
echo "📂 Open your browser and navigate to: http://localhost"
echo ""
echo "Containers status:"
$COMPOSE_CMD ps

echo ""
echo "To stop the application: $COMPOSE_CMD down"
