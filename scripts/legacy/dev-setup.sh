#!/bin/bash
set -e

echo "🚀 Setting up DECIES development environment..."

# Copy env files
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env"
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
fi

# Install dependencies
echo "📦 Installing dependencies..."
make install

# Start Docker
echo "🐳 Starting Docker services..."
make dev-up

echo ""
echo "✅ Setup complete!"
echo "Backend: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
