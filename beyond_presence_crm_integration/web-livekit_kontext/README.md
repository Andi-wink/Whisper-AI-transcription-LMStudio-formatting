# 🌐 LiveKit Support Agent with BeyondPresence Avatar

[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![LiveKit](https://img.shields.io/badge/LiveKit-Cloud-orange)](https://livekit.io/cloud)
[![Groq](https://img.shields.io/badge/LLM-Groq-purple)](https://groq.com/)

A **real-time AI voice/video support agent** built with **LiveKit**, **BeyondPresence avatars**, and **Groq LLM**.  
Includes a **Next.js frontend** for customer interactions and multiple **Python agent variants** for different use cases.

---

## ✨ Features
- 🧑‍💻 Next.js frontend with voice & video agent modes
- 🐍 Multiple Python agents for different scenarios
- 🔑 Server-side JWT token generation (no static client tokens)
- 🤖 BeyondPresence avatar integration for video mode
- ⚡ **Groq LLM** (Llama 3.3 70B) for ultra-fast responses
- 🎙️ Deepgram STT + Cartesia TTS for natural speech
- 🔧 Built-in tools: HubSpot CRM, call summaries, insurance quotes
- 🚀 Deploy to LiveKit Cloud or self-host with Docker

---

## 🤖 Included Agents

| Agent | File | Description |
|-------|------|-------------|
| **Basic Support** | `demo_1_basic.py` | Voice-only insurance support agent with Groq LLM |
| **German Agent** | `demo_2_german.py` | German language support agent |
| **Avatar Agent** | `demo_3_avatar.py` | Full video avatar with BeyondPresence integration |
| **Handoff Agent** | `demo_4_handoff.py` | Agent with human handoff capability |

## 🔧 Built-in Tools

The agents include function-calling tools:

| Tool | Description |
|------|-------------|
| `get_insurance_quote` | Generate insurance quotes based on customer details |
| `lookup_policy` | Look up existing policy information |
| `schedule_callback` | Schedule a callback with a human agent |
| `hubspot_integration` | Sync call data with HubSpot CRM |
| `call_summary` | Auto-generate call summaries sent to n8n webhook |

## 🧠 AI Stack

| Component | Provider | Model/Service |
|-----------|----------|---------------|
| **LLM** | Groq | Llama 3.3 70B Versatile |
| **STT** | Deepgram | Nova-2 |
| **TTS** | Cartesia | Sonic Turbo |
| **VAD** | Silero | Voice Activity Detection |
| **Avatar** | BeyondPresence | Hyper-realistic video avatar |

---

## ⚡ Prerequisites
You’ll need:
- [Node.js](https://nodejs.org/) **v18+**
- [Python](https://www.python.org/) **3.10+**
- A [LiveKit Cloud](https://livekit.io/cloud) project (URL, API Key, API Secret)
- A **Groq API key** (free tier available)
- A **Deepgram API key** (for speech-to-text)
- A **Cartesia API key** (for text-to-speech)
- Optional: **BeyondPresence API key** (for avatar mode)

---

## Step 0 

```bash
git clone https://github.com/Andi-wink/Support-Agent.git
cd Support-Agent/
```

## 📦 Step 1 — Install dependencies
From the project root:

```bash
pnpm install   # or: npm install
```

## 🔑 Step 2 — Configure environment variables (secure)

Create `.env.local` in project root for the Next.js app:

```bash
NEXT_PUBLIC_BEY_API_KEY=your_beyondpresence_api_key
NEXT_PUBLIC_DEMO_AVATAR_ID=your_avatar_id
NEXT_PUBLIC_DEMO_LIVEKIT_URL=wss://your-project.livekit.cloud

LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

Create `python-agent/.env` for the Python agent:

```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Services (Required)
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key

# BeyondPresence Avatar (for demo_3_avatar.py)
BEY_API_KEY=your_beyondpresence_api_key
BEYOND_PRESENCE_AVATAR_ID=your_avatar_id

# Optional: HubSpot Integration
HUBSPOT_ACCESS_TOKEN=your_hubspot_token

# Optional: n8n Webhook for Call Summaries
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/call-summary
```

Notes:
- The web app auto-generates viewer JWTs using `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`. You do not need to provide a static `NEXT_PUBLIC_DEMO_LIVEKIT_TOKEN`.
- Use the same LiveKit URL/key/secret in both apps.

## ▶️ Step 3 — Start a Python agent

Terminal 1 — Choose an agent to run:

```bash
cd python-agent

# Basic voice agent (no avatar)
python demo_agents/demo_1_basic.py dev

# German language agent
python demo_agents/demo_2_german.py dev

# Avatar agent (requires BeyondPresence)
python demo_agents/demo_3_avatar.py dev

# Handoff agent
python demo_agents/demo_4_handoff.py dev
```

The `dev` command connects to LiveKit and waits for room connections from the web app.

## 🌐 Step 4 — Start the Next.js app

Terminal 2:

```bash
pnpm dev  # or: npm run dev
```

Open `http://localhost:3000` and you should see the avatar stream. The app will show a configuration warning page until required env vars are set.

## 🧭 How it works (flow)

Python Agent  ➜  LiveKit Cloud  ➜  Next.js Viewer

The Python agent connects to LiveKit and publishes audio/video for the chosen avatar.

The Next.js app requests a server-generated JWT and joins the LiveKit room.

The viewer plays the avatar stream in real time.

## 🛠 Troubleshooting

❌ No video/audio → Ensure the Python agent is running and connected to LiveKit.

🔑 Token errors → Check LIVEKIT_API_KEY/LIVEKIT_API_SECRET in both .env.local and python-agent/.env.

🚫 401/403 from LiveKit → Verify LIVEKIT_URL and that the project credentials match.

🤖 Groq errors → Confirm GROQ_API_KEY is set in python-agent/.env.

🔇 Autoplay blocked → Click anywhere in the page to enable audio playback.

🧪 Windows/WSL path issues → Prefer running the repo under your Linux home (e.g., ~/project) instead of /mnt/c/....

## 🧳 Scripts
**Web**

  pnpm dev — run dev server
  
  pnpm build — build for production
  
  pnpm start — start production server
  
  pnpm test — run tests

**Python**

  python-agent/run-uv.sh — run agent with uv
  
  python-agent/run.sh — run agent with venv + pip


## Structure of the codebase

```bash
.
├─ python-agent/
│  ├─ demo_agents/           # Agent variants
│  │  ├─ demo_1_basic.py     # Voice-only support agent
│  │  ├─ demo_2_german.py    # German language agent
│  │  ├─ demo_3_avatar.py    # Avatar agent (BeyondPresence)
│  │  └─ demo_4_handoff.py   # Human handoff agent
│  ├─ agents/                # Shared agent classes
│  ├─ integrations/          # HubSpot, call summaries
│  ├─ tools/                 # Insurance quote tools
│  ├─ config.py              # Shared configuration
│  ├─ Dockerfile             # Cloud deployment
│  └─ .env                   # API keys (not committed)
├─ src/
│  ├─ app/                   # Next.js pages & API routes
│  ├─ components/            # React components
│  └─ lib/
│     ├─ beyondpresence/     # Avatar SDK wrapper
│     └─ auth/               # Authentication
├─ e2e/                      # Playwright tests
├─ .env.local                # Frontend env (not committed)
└─ package.json
```

## 📝 Note
Make sure environment files are **ignored**:

```bash
.env
*.env
**/*.env
.env.local
python-agent/.env
```

Add env files to .gitignore:
