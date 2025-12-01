#!/bin/bash
set -e

echo "🚀 Starting docs-pipeline web demo..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found, using 'docker compose' instead"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Build Docker images
echo "📦 Building Docker images (this may take a few minutes on first run)..."
$COMPOSE_CMD build

echo ""
echo "🔄 Starting services..."
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if service is healthy
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo ""
        echo "✅ ✅ ✅ Demo is ready! ✅ ✅ ✅"
        echo ""
        echo "🌐 Open your browser to: http://localhost:8080"
        echo ""
        echo "📝 To stop the demo:"
        echo "   $COMPOSE_CMD down"
        echo ""
        echo "📋 To view logs:"
        echo "   $COMPOSE_CMD logs -f"
        echo ""
        exit 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

echo ""
echo "⚠️  Service didn't start within expected time. Checking logs..."
$COMPOSE_CMD logs

exit 1

