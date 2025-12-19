# BeyondPresence Python Agent

This Python agent handles the AI avatar integration with BeyondPresence using the official LiveKit plugin, while your Next.js frontend displays the video stream.

## Setup

1. **Install Python 3.10+**
   ```bash
   python3 --version  # Should be 3.10 or higher
   ```

2. **Add your API Keys**
   
   Edit `python-agent/.env` and add your keys:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   DEEPGRAM_API_KEY=your-deepgram-key-here  # Optional but recommended
   ```
   
   - Get OpenAI API key from: https://platform.openai.com/api-keys
   - Get free Deepgram key from: https://deepgram.com (better speech recognition)

3. **Run the agent**

   **Option A: Using pip (traditional)**
   ```bash
   cd python-agent
   ./run.sh
   ```

   **Option B: Using uv (faster)**
   ```bash
   cd python-agent
   ./run-uv.sh
   ```

   Or directly with uv:
   ```bash
   uv run python agent.py dev
   ```

## How It Works

1. **Python Agent** (this directory):
   - Connects to LiveKit as an agent
   - Creates BeyondPresence avatar session using official plugin
   - Routes audio through data channels to avatar (critical!)
   - Avatar generates synchronized video+audio and publishes to room
   - Uses PipelineAgent with STT, LLM, and TTS components

2. **Next.js Frontend** (parent directory):
   - Connects to the same LiveKit room as viewer
   - Subscribes to avatar's video stream
   - Displays the video on your localhost website

## Running the Full System

1. **Terminal 1 - Start Python Agent:**
   ```bash
   cd python-agent
   ./run.sh
   ```
   Wait for: "Starting agent for room: avatar-room-..."

2. **Terminal 2 - Start Next.js Frontend:**
   ```bash
   cd ..  # Go to project root
   npm run dev
   ```

3. **Browser:**
   - Open http://localhost:3000
   - The avatar video should appear automatically
   - The AI will greet you and respond to conversation

## Troubleshooting

- **No video appearing?** Check that the Python agent is running and connected
- **OpenAI error?** Verify your OPENAI_API_KEY in `.env`
- **Connection issues?** Check LiveKit credentials match in both `.env` files

## Architecture

```
Python Agent → Creates Avatar → Publishes to LiveKit Room
                                          ↓
Frontend → Joins Same Room → Subscribes to Video → Displays on Website
```

The Python agent and frontend are separate processes that communicate through LiveKit's infrastructure.