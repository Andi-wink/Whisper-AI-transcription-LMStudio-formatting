# Demo Agents

Four agent variants for demonstration purposes.

## Run All 4 Simultaneously

Double-click to start all agents in separate windows:
```
demo_agents\run_all.bat
```

Or manually open 4 terminals and run each:

```bash
# Terminal 1
python demo_agents/demo_1_basic.py start

# Terminal 2
python demo_agents/demo_2_german.py start

# Terminal 3
python demo_agents/demo_3_avatar.py start

# Terminal 4
python demo_agents/demo_4_handoff.py start
```

## Connect to Specific Agent

Each agent has a unique name. Use the playground with `?agent=` parameter:

| Agent | Playground URL |
|-------|----------------|
| **Basic** | `https://agents-playground.livekit.io/?agent=demo-basic` |
| **German** | `https://agents-playground.livekit.io/?agent=demo-german` |
| **Avatar** | `https://agents-playground.livekit.io/?agent=demo-avatar` |
| **Handoff** | `https://agents-playground.livekit.io/?agent=demo-handoff` |

Open 4 browser windows, each with a different URL above.

---

## Quick Start (Single Agent)

From the `python-agent` directory:

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run any demo
python demo_agents/demo_1_basic.py start
```

---

## Demo 1: Basic Insurance Agent
**File:** `demo_1_basic.py`

Standard insurance support agent with:
- Policy lookup from HubSpot
- Address updates
- Registration plate updates
- Support ticket creation

```bash
python demo_agents/demo_1_basic.py start
```

---

## Demo 2: German-Speaking Agent
**File:** `demo_2_german.py`

Bilingual agent (German/English):
- Greets in German: "Guten Tag!"
- Switches language based on user
- Same tools as basic agent

```bash
python demo_agents/demo_2_german.py start
```

**Tip:** Set `ELEVENLABS_GERMAN_VOICE_ID` for a German voice.

---

## Demo 3: Beyond Presence Avatar
**File:** `demo_3_avatar.py`

Visual avatar representation:
- Requires `BEYOND_PRESENCE_AVATAR_ID` or `BEY_AVATAR_ID`
- Same tools as basic agent

```bash
python demo_agents/demo_3_avatar.py start
```

**Required env vars:**
- `BEY_API_KEY`
- `BEYOND_PRESENCE_AVATAR_ID`

---

## Demo 4: Multi-Agent Handoff
**File:** `demo_4_handoff.py`

Two-agent system with transfers:
- **Support Agent**: General inquiries, policy, address updates
- **Claims Agent**: Filing claims, claim status

User says "I want to file a claim" → Transfers to Claims Agent
User says "I have a general question" → Transfers back to Support

```bash
python demo_agents/demo_4_handoff.py start
```

---

## Environment Variables Required

```env
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# LLM & Voice
GROQ_API_KEY=your_groq_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# CRM
HUBSPOT_ACCESS_TOKEN=your_hubspot_token

# Avatar (Demo 3 only)
BEY_API_KEY=your_bey_key
BEYOND_PRESENCE_AVATAR_ID=your_avatar_id
```

---

## Playground URL

Connect to test: https://agents-playground.livekit.io
