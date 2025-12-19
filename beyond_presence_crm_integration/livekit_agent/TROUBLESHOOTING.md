# Troubleshooting Guide

## Issue 1: Agent Won't Connect (FIXED ✅)

**Error**: `failed to connect to livekit after 16 attempts`

**Solution**: Add `--bind 0.0.0.0` to the Docker command:
```bash
docker run -p 7880:7880 -p 7881:7881 -p 7882:7882 livekit/livekit-server --dev --bind 0.0.0.0
```

## Issue 2: Beyond Presence DNS Error (FIXED ✅)

**Error**: `Cannot connect to host api.beyondpresence.ai:443`

**Cause**: No internet access to Beyond Presence API OR missing API key.

**Solution**: The agent now runs in **audio-only mode** without Beyond Presence. You'll see this log:
```
Beyond Presence credentials not set. Agent will run in audio-only mode.
```

This is normal for local testing. The agent voice will still work via OpenAI TTS.

## Issue 3: Browser WebRTC Connection Fails

**Error in browser**: `Connection failed: could not establish pc connection`

**Cause**: The browser cannot establish a WebRTC connection to the local LiveKit server due to NAT/firewall issues.

### Quick Fixes to Try:

#### Option A: Use localhost in browser
1. Make sure you're accessing `index.html` from `http://localhost` (not `file://`)
2. Run: `python -m http.server 8000` in the `livekit_agent` folder
3. Open: `http://localhost:8000/index.html`

#### Option B: Simplify Docker networking
Instead of port mapping, try Docker host network mode (Linux/Mac only):
```bash
docker run --network=host livekit/livekit-server --dev
```

On Windows, use the regular port mapping command but ensure Windows Firewall allows connections.

#### Option C: Check .env settings
Your `.env` should have:
```properties
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=sk-...  # REQUIRED for voice
```

#### Option D: Restart everything in order
1. Stop the agent (Ctrl+C)
2. Stop Docker (Ctrl+C)
3. Start Docker: `docker run -p 7880:7880 -p 7881:7881 -p 7882:7882 livekit/livekit-server --dev --bind 0.0.0.0`
4. Wait for "starting LiveKit server" message
5. Start agent: `python agent.py start`
6. Wait for "registered worker" message
7. Open browser to `http://localhost:8000`

## What's Working Now

✅ Docker server starts correctly  
✅ Agent connects to LiveKit server  
✅ Agent runs without Beyond Presence  
✅ Token is hardcoded in webpage  
❓ Browser → LiveKit WebRTC connection (needs testing)

## Next Steps if Still Not Working

If the browser still can't connect, we might need to:
1. Use LiveKit Cloud instead of local server (easiest)
2. Configure TURN server for NAT traversal
3. Use `ngrok` or similar tunneling service
