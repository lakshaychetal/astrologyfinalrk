#!/bin/bash

# Local development setup and run script
# For Mac/Linux

echo "🚀 Setting up Vedic Astrology AI..."
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Setup environment file
echo "⚙️  Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Created .env file"
    echo "⚠️  Please edit .env and add your GOOGLE_CLOUD_API_KEY"
    echo ""
fi

# Run application
echo "🌟 Starting Vedic Astrology AI..."
echo "📊 Configuration:"
echo "   Project: superb-analog-464304-s0"
echo "   Region: asia-south1"
echo "   Model: gemini-1.5-flash"
echo "   Port: 8080"
echo ""
echo "📱 Open browser to: http://127.0.0.1:7860"
echo "🛑 Press Ctrl+C to stop"
echo ""

python main.py

