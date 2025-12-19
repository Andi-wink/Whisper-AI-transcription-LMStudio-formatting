# 🚀 Setup Guide for Windows

## ✅ Completed Steps
- [x] Repository cloned
- [x] Python dependencies installed in `python-agent/venv`

## 📋 Next Steps

### 1. Get API Credentials

You need three sets of credentials:

#### A. LiveKit Cloud (Free Tier Available)
1. Sign up at: https://cloud.livekit.io/
2. Create a new project
3. Get your credentials:
   - WebSocket URL: `wss://your-project.livekit.cloud`
   - API Key
   - API Secret

#### B. Beyond Presence
- ✅ You mentioned you have this
- Get Avatar ID from your dashboard

#### C. OpenAI
- Get API key from: https://platform.openai.com/api-keys

---

### 2. Create Environment Files

#### File 1: `.env.local` (in root folder)
Create file: `web-livekit_kontext\.env.local`

```env
NEXT_PUBLIC_BEY_API_KEY=your_beyondpresence_api_key
NEXT_PUBLIC_DEMO_AVATAR_ID=your_avatar_id
NEXT_PUBLIC_DEMO_LIVEKIT_URL=wss://your-project.livekit.cloud

LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

#### File 2: `python-agent\.env`
Create file: `python-agent\.env`

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

OPENAI_API_KEY=sk-your-openai-key
BEY_AVATAR_ID=your_avatar_id

# Optional personalization
PT_USER_NAME=Your Name
PT_USER_CONTEXT=Brief description
PT_LLM_MODEL=gpt-4o-mini
PT_TTS_VOICE=alloy
```

---

### 3. Install Node.js Dependencies

Open PowerShell in the `web-livekit_kontext` folder:

```powershell
# Option 1: Using pnpm (faster)
npm install -g pnpm
pnpm install

# Option 2: Using npm
npm install
```

---

### 4. Start the Application

#### Terminal 1: Start Python Agent
```powershell
cd python-agent
.\run.bat
```

Or manually:
```powershell
cd python-agent
.\venv\Scripts\activate
python agent.py dev
```

#### Terminal 2: Start Next.js Web App
```powershell
# Using pnpm
pnpm dev

# Or using npm
npm run dev
```

---

### 5. Open Browser

Navigate to: http://localhost:3000

You should see the Beyond Presence avatar streaming!

---

## 🛠 Troubleshooting

### Python Agent Won't Start
- ✅ Check `python-agent\.env` exists with all values
- ✅ Verify LiveKit credentials are correct
- ✅ Ensure OpenAI API key is valid

### Web App Shows Config Warning
- ✅ Check `.env.local` exists in root folder
- ✅ Verify all variables start with `NEXT_PUBLIC_` for public vars
- ✅ Restart the dev server after creating .env.local

### No Avatar Video/Audio
- ✅ Make sure Python agent is running first
- ✅ Check browser console for errors
- ✅ Verify Beyond Presence API key and Avatar ID
- ✅ Click anywhere on page to enable autoplay

### LiveKit Connection Errors
- ✅ Verify WebSocket URL starts with `wss://`
- ✅ Check API Key and Secret match between both .env files
- ✅ Ensure LiveKit project is active

---

## 📁 File Structure

```
web-livekit_kontext/
├── .env.local                    # ← CREATE THIS (Next.js config)
├── python-agent/
│   ├── .env                      # ← CREATE THIS (Python config)
│   ├── venv/                     # ✅ Already created
│   ├── agent.py                  # Main agent code
│   └── run.bat                   # ✅ Windows launcher
├── src/                          # Next.js source
├── package.json
└── README.md
```

---

## 🎯 Quick Start Checklist

- [ ] Create `.env.local` in root
- [ ] Create `python-agent\.env`
- [ ] Install Node.js dependencies (`pnpm install` or `npm install`)
- [ ] Start Python agent (`python-agent\run.bat`)
- [ ] Start Next.js app (`pnpm dev`)
- [ ] Open http://localhost:3000

---

## 💡 Tips

1. **Use Chrome/Edge** for best WebRTC support
2. **Use headphones** to prevent audio feedback
3. **Keep both terminals open** while testing
4. **Check browser console** (F12) for detailed errors
5. **Python agent logs** will show connection status

---

## 📚 Resources

- LiveKit Docs: https://docs.livekit.io/
- Beyond Presence: https://beyondpresence.ai/
- OpenAI API: https://platform.openai.com/docs
- Project GitHub: https://github.com/vrk7/web-livekit_kontext

---

**Ready to test your interactive avatar!** 🎉
