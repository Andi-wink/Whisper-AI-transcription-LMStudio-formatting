# LiveKit + Beyond Presence Interactive Avatar Test

Minimal test project for interactive avatar with voice conversation and video lip sync.

## 🎯 Features

- ✅ Voice conversation (Speech-to-Text + Text-to-Speech)
- ✅ Video avatar with lip sync via Beyond Presence
- ✅ Python backend agent
- ✅ Web-based frontend interface
- ✅ Real-time audio/video streaming

## 📋 Prerequisites

1. **LiveKit Account** (Free tier available)
   - Sign up at: https://livekit.io/
   - Get your API Key, Secret, and WebSocket URL
   - Create a room token

2. **Beyond Presence API**
   - API Key
   - Avatar ID

3. **OpenAI API Key** (for STT/TTS)
   - Get from: https://platform.openai.com/

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd livekit_agent
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
LIVEKIT_URL=wss://your-server.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
BEYOND_PRESENCE_API_KEY=your_beyond_presence_key
BEYOND_PRESENCE_AVATAR_ID=your_avatar_id
OPENAI_API_KEY=your_openai_key
```

### 3. Run the Agent

```bash
python agent.py start
```

The agent will connect to LiveKit and wait for participants.

### 4. Open the Web Interface

1. Open `index.html` in a web browser
2. Enter your LiveKit WebSocket URL
3. Generate a room token using LiveKit CLI or dashboard
4. Enter the token and click "Connect to Room"

## 🔑 Getting a Room Token

### Option 1: LiveKit CLI
```bash
livekit-cli token create \
  --api-key <your_api_key> \
  --api-secret <your_api_secret> \
  --join --room test-room \
  --identity user1 \
  --valid-for 24h
```

### Option 2: LiveKit Dashboard
- Go to your LiveKit Cloud dashboard
- Navigate to "Tokens" section
- Generate a new token with room permissions

### Option 3: Python Script
```python
from livekit import api
import os

token = api.AccessToken(
    os.getenv("LIVEKIT_API_KEY"),
    os.getenv("LIVEKIT_API_SECRET")
)
token.with_identity("user1").with_name("Test User").with_grants(
    api.VideoGrants(room_join=True, room="test-room")
)
print(token.to_jwt())
```

## 🎮 How to Test

1. **Start the agent** (in terminal):
   ```bash
   python agent.py start
   ```

2. **Open `index.html`** in browser

3. **Connect to room** with your token

4. **Speak** - The avatar will:
   - Listen to your speech (STT)
   - Process with AI (LLM)
   - Respond with voice (TTS)
   - Display lip-synced video avatar

## 🔧 Troubleshooting

### Agent won't start
- Check `.env` file has all required credentials
- Verify LiveKit credentials are correct
- Ensure OpenAI API key is valid

### Can't connect from browser
- Verify WebSocket URL starts with `wss://`
- Check room token is not expired
- Ensure agent is running before connecting

### No audio/video
- Check browser permissions for microphone
- Verify Beyond Presence avatar ID is correct
- Check browser console for errors

### Voice not working
- Verify OpenAI API key has sufficient credits
- Check microphone permissions in browser
- Look at agent logs for errors

## 📝 Project Structure

```
livekit_agent/
├── agent.py              # Python backend agent
├── index.html            # Web frontend
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── .env                  # Your credentials (gitignored)
└── README.md            # This file
```

## 🔄 Next Steps

After successful testing:

1. **Customize the AI prompt** in `agent.py` (line 74)
2. **Integrate Beyond Presence avatar rendering**
3. **Add custom wake words or commands**
4. **Deploy to production** with proper authentication

## 📚 Documentation

- LiveKit Agents: https://docs.livekit.io/agents/
- Beyond Presence API: https://docs.beyondpresence.ai/
- OpenAI API: https://platform.openai.com/docs

## 🐛 Known Issues

- Beyond Presence integration is basic (fetches config only)
- No persistent conversation history
- Single user per room only

## 💡 Tips

- Use headphones to prevent audio feedback
- Test with Chrome/Edge for best WebRTC support
- Keep browser console open to monitor connection
- Check agent terminal for detailed logs
