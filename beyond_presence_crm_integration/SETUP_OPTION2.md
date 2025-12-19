# Complete Setup Guide - Option 2 (LiveKit with Tools)

Step-by-step guide to get your website with avatar + CRM tools running.

---

## 🎯 What You're Building

**Your Website** → **LiveKit** → **Your Agent (with CRM tools)** → **Beyond Presence Avatar**

---

## ⚡ Quick Setup (30 minutes)

### Phase 1: Prepare Agent (10 min)

#### 1. Update ClickUp Integration

Edit `livekit_agent/crm_agent.py`:

```python
# Line ~30: Replace CRMClient with real ClickUp
from examples.crm_integrations.clickup_example import ClickUpCRM

class CRMVoiceAgent(VoiceAgent):
    def __init__(self):
        # Use your actual ClickUp credentials
        self.crm = ClickUpCRM(
            api_token="pk_68582715_2FDIJNPRG2C4AZ3EKG563NN83H20Q6G1",
            list_id="901513394496"
        )
```

#### 2. Configure Environment

Edit `livekit_agent/.env`:

```bash
# LiveKit (get from cloud.livekit.io)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxx

# Beyond Presence (get from app.bey.chat)
BEYOND_PRESENCE_API_KEY=sk-your-api-key
BEYOND_PRESENCE_AVATAR_ID=your-avatar-id

# LLM
OPENAI_API_KEY=sk-your-openai-key

# STT/TTS
DEEPGRAM_API_KEY=your-deepgram-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# CRM
CLICKUP_API_TOKEN=pk_68582715_2FDIJNPRG2C4AZ3EKG563NN83H20Q6G1
CLICKUP_LIST_ID=901513394496
```

#### 3. Test Agent Locally

```bash
cd livekit_agent
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python crm_agent.py dev
```

Should see: `✓ Connected to LiveKit server`

#### 4. Deploy Agent

```bash
livekit-cli agent deploy crm_agent.py \
  --name production-agent \
  --env-file .env \
  --auto-scale
```

Verify: `livekit-cli agent list`

---

### Phase 2: Deploy Token Server (5 min)

#### 1. Configure Token Server

Edit `website_example/.env`:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxx
```

#### 2. Test Locally

```bash
cd website_example
pip install -r requirements.txt
python token_server.py
```

Test: `curl http://localhost:3000/api/get-token`

#### 3. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# Get URL: https://your-app.railway.app
```

**Save this URL!** You'll need it for the website.

---

### Phase 3: Deploy Website (5 min)

#### 1. Update Configuration

Edit `website_example/index.html` line ~90:

```javascript
const CONFIG = {
  tokenEndpoint: 'https://your-app.railway.app/api/get-token'
  // Replace with your Railway URL
};
```

#### 2. Test Locally

```bash
cd website_example
python -m http.server 8000
```

Open: http://localhost:8000

#### 3. Deploy to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd website_example
netlify deploy --prod

# Or drag & drop folder to netlify.com
```

**Save this URL!** This is your live website.

---

### Phase 4: Test Everything (10 min)

#### 1. Open Your Website

Go to: `https://your-site.netlify.app`

#### 2. Start Conversation

1. Click "Start Conversation"
2. Allow microphone
3. Wait for avatar video
4. Say: "Hi, I'm testing"

#### 3. Test CRM Tools

```
You: "Look up my account, phone is 555-0123"
Avatar: [Calls CRM tool, responds with customer data]

You: "Create a lead for John Doe, email john@example.com"
Avatar: [Creates lead in ClickUp]
```

#### 4. Verify in ClickUp

Go to: https://app.clickup.com/12345/v/li/901513394496

Check for new lead created by avatar.

---

## 🎬 Demo Script for Your Client

Give this to your non-technical client:

### Demo Instructions

**Website URL:** `https://your-site.netlify.app`

**What to do:**
1. Open the website
2. Click "Start Conversation"
3. Allow microphone when prompted
4. Wait 2-3 seconds for avatar to appear
5. Start talking!

**What to say:**
- "Hi, I need help with my account"
- "Look up my account, my phone is 555-0123"
- "I want to place an order"
- "Create a lead for [Name], email [email@example.com]"

**Check results:**
- Go to ClickUp: https://app.clickup.com/12345/v/li/901513394496
- See new leads created automatically

**If something doesn't work:**
- Refresh the page
- Check microphone permissions
- Try a different browser (Chrome recommended)
- Text me: [Your Number]

---

## 🔧 Maintenance (For You)

### Update Agent Code

```bash
# 1. Edit crm_agent.py on your machine
# 2. Test locally
python crm_agent.py dev

# 3. Deploy update
livekit-cli agent deploy crm_agent.py --update

# Zero downtime - LiveKit handles rollout
```

### View Logs

```bash
# Agent logs
livekit-cli agent logs production-agent

# Token server logs
# Check Railway dashboard

# Website logs
# Check Netlify dashboard
```

### Scale for Big Demo

```bash
# Before demo
livekit-cli agent scale production-agent --replicas 5

# After demo
livekit-cli agent scale production-agent --replicas 1
```

---

## 💰 Cost Estimate

For demo usage (10 calls/day, 3 min avg):

```
LiveKit Cloud: $0.42/day
Beyond Presence: $4.50/day
OpenAI: $0.30/day
Deepgram: $0.13/day
ElevenLabs: $0.50/day
Railway (token server): $5/month
Netlify (website): Free
---
Daily: ~$5.85
Monthly: ~$180
```

---

## ✅ Pre-Demo Checklist

Send this to your client 24 hours before demo:

```
□ Test website loads
□ Test "Start Conversation" button works
□ Test microphone permission
□ Test avatar appears
□ Test CRM lookup: "Look up account 555-0123"
□ Test lead creation: "Create lead for John Doe"
□ Verify ClickUp shows new records
□ Prepare demo script
□ Have backup plan (your phone number)
```

---

## 🆘 Emergency Troubleshooting

### Avatar Not Appearing

```bash
# Check agent status
livekit-cli agent list

# Restart agent
livekit-cli agent restart production-agent

# Check logs
livekit-cli agent logs production-agent
```

### Token Server Down

```bash
# Check Railway dashboard
# View logs
# Restart service

# Or use backup token server
# Update website CONFIG.tokenEndpoint
```

### CRM Not Updating

```python
# Test ClickUp connection
python
>>> from examples.crm_integrations.clickup_example import ClickUpCRM
>>> crm = ClickUpCRM("pk_...", "901513394496")
>>> result = await crm.lookup_customer("+1-555-0123")
>>> print(result)
```

---

## 🎯 Success Metrics

Track these after deployment:

- **Uptime**: Should be 99%+
- **Response Time**: Avatar should respond in <3 seconds
- **CRM Accuracy**: 95%+ correct data extraction
- **User Satisfaction**: Collect feedback
- **Cost per Call**: Should be ~$0.60

---

## 📞 Support Contacts

**For Your Client:**
- Your Phone: [Your Number]
- Your Email: [Your Email]
- Website Issues: Check Netlify status
- CRM Issues: Check ClickUp

**For You:**
- LiveKit Discord: https://livekit.io/discord
- Beyond Presence: support@beyondpresence.ai
- Railway Support: help@railway.app

---

## 🚀 Next Steps

After successful demo:

1. **Collect Feedback**
   - What worked well?
   - What needs improvement?
   - What features to add?

2. **Optimize**
   - Improve agent prompts
   - Add more CRM tools
   - Enhance error handling

3. **Scale**
   - Increase agent replicas
   - Add monitoring
   - Set up alerts

4. **Expand**
   - Add more integrations
   - Multi-language support
   - Advanced analytics

---

## 📚 Documentation Links

- **Main README**: `../README.md`
- **Website Integration Guide**: `livekit_agent/website_integration_guide.md`
- **Website Example**: `website_example/README.md`
- **Agent Code**: `livekit_agent/crm_agent.py`
- **ClickUp Integration**: `examples/crm_integrations/clickup_example.py`

---

## ✨ You're Done!

Your client now has:
- ✅ Professional website with AI avatar
- ✅ Real-time CRM integration
- ✅ Automatic lead creation
- ✅ Zero maintenance required
- ✅ Scalable infrastructure

They just need to:
- 📞 Share the website URL
- 🎤 Let customers talk to the avatar
- 📊 Check ClickUp for new leads

**You can update everything remotely without their involvement!**
