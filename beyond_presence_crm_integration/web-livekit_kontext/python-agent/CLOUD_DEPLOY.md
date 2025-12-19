# Deploying Agents to LiveKit Cloud

LiveKit Cloud can host your agents so they run 24/7 without manual startup.

## Option 1: LiveKit CLI Deploy (Easiest)

### 1. Install LiveKit CLI
```bash
# Windows (PowerShell as Admin)
winget install livekit.livekit-cli

# Or download from: https://github.com/livekit/livekit-cli/releases
```

### 2. Authenticate with LiveKit Cloud
```bash
lk cloud auth
```

### 3. Deploy your agent
```bash
cd python-agent
lk cloud deploy --project support-agent-me7v9squ
```

The CLI will:
- Build your Docker image
- Push it to LiveKit's registry
- Deploy and run it on their infrastructure

## Option 2: Docker + Cloud Run/Railway/Fly.io

If you prefer to host elsewhere but connect to LiveKit Cloud:

### 1. Build the Docker image
```bash
cd python-agent
docker build -t livekit-agent .
```

### 2. Push to your registry
```bash
docker tag livekit-agent your-registry/livekit-agent
docker push your-registry/livekit-agent
```

### 3. Deploy with environment variables
Set these env vars in your hosting platform:
- `LIVEKIT_URL=wss://support-agent-me7v9squ.livekit.cloud`
- `LIVEKIT_API_KEY=your-key`
- `LIVEKIT_API_SECRET=your-secret`
- `GROQ_API_KEY=your-groq-key`
- `DEEPGRAM_API_KEY=your-deepgram-key`
- `CARTESIA_API_KEY=your-cartesia-key`
- `BEY_API_KEY=your-bey-key` (for avatar)
- `BEYOND_PRESENCE_AVATAR_ID=your-avatar-id` (for avatar)

## Option 3: Run Locally with Auto-Restart

For development/testing, use a process manager:

### Windows (NSSM)
```bash
# Install NSSM: https://nssm.cc/download
nssm install LiveKitAgent "python" "demo_agents/demo_1_basic.py start"
nssm set LiveKitAgent AppDirectory "C:\path\to\python-agent"
nssm start LiveKitAgent
```

### Or use PM2 (cross-platform)
```bash
npm install -g pm2
pm2 start "python demo_agents/demo_1_basic.py start" --name livekit-agent
pm2 save
pm2 startup
```

## Switch Between Agents

To deploy the avatar agent instead of basic:
```bash
# Edit Dockerfile CMD line to:
CMD ["uv", "run", "python", "demo_agents/demo_3_avatar.py", "start"]
```

## Verify Deployment

Once deployed, test with:
```bash
python generate_playground_link.py "Test User"
```

The agent should connect automatically when you join the playground room.
