#!/bin/bash

# Task & Project Management SaaS - Run Script

# 1. Generate keys if they don't exist
if [ ! -f keys/private.pem ]; then
    echo "Generating RSA keys..."
    python3 scripts/generate_keys.py
fi

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
fi

# 3. Build and run docker containers
echo "Building and starting services..."
docker-compose up --build -d

echo ""
echo "✅ System started successfully!"
echo   
echo "API Gateway:      http://localhost:8000/docs"
echo "Auth Service:     http://localhost:8001/docs"
echo "Org Service:      http://localhost:8002/docs"
echo "Project Service:  http://localhost:8003/docs"
echo "Task Service:     http://localhost:8004/docs"
echo "Notification Svc: http://localhost:8005/docs"
echo "File Service:     http://localhost:8006/docs"
echo   
echo "To view logs: docker-compose logs -f"
