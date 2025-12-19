#!/bin/bash

# Setup and run the Python agent for BeyondPresence avatar

echo "🚀 Starting BeyondPresence Python Agent..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set in .env file!"
    echo "Please add your OpenAI API key to python-agent/.env"
    echo "Example: OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

# Run the agent
echo "🤖 Starting agent..."
echo "The agent will join rooms with prefix 'avatar-room-'"
echo "Your frontend will connect to the same room to view the avatar"
echo ""
python agent.py