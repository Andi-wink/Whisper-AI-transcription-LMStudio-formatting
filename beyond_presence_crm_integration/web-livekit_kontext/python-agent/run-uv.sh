#!/bin/bash

# Run the Python agent using uv (fast Python package manager)

echo "🚀 Starting BeyondPresence Python Agent with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set in .env file!"
    echo "Please add your OpenAI API key to python-agent/.env"
    echo "Example: OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

# Run the agent with uv
echo "🤖 Starting agent with uv..."
echo "The agent will join any LiveKit room and add an avatar to it"
echo ""

# Use uv to run the agent with dependencies
uv run --with livekit-agents \
       --with livekit-plugins-openai \
       --with livekit-plugins-bey \
       --with livekit-plugins-deepgram \
       --with livekit-plugins-silero \
       --with python-dotenv \
       python agent.py dev