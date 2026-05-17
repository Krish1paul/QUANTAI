#!/bin/bash
echo "Starting Enhanced Trading Agent API..."
echo "===================================="

# Navigate to api directory
cd api

# Kill any existing processes
pkill -f simple_api.py 2>/dev/null

# Start the API
python simple_api.py &

# Wait for API to start
echo "Waiting for API to start..."
sleep 5

# Check if API is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ API is running!"
    echo "API Health: $(curl -s http://localhost:8001/health | jq -r '.status')"
    echo "API Documentation: http://localhost:8001/docs"
    echo ""
    echo "Test endpoints:"
    echo "  curl http://localhost:8001/"
    echo "  curl http://localhost:8001/health"
    echo "  curl http://localhost:8001/signal/AAPL"
else
    echo "❌ API failed to start"
    echo "Check api.log for errors"
fi