# Beyond Presence Avatar CRM Integration

This project provides two architecture options for integrating your Beyond Presence avatar with CRM systems, enabling capabilities like:
- **Update CRM records** (create/update leads, contacts, opportunities)
- **Retrieve CRM information** (lookup customer data, order history, account details)
- **Forward/transfer calls** (route to human agents, departments, or phone numbers)

---

## 🎯 Option 1: n8n Backend (Recommended for No-Code/Low-Code)

### Architecture Overview
```
Beyond Presence Avatar (Managed Agent)
    ↓ (webhooks)
n8n Workflows
    ↓ (API calls)
Your CRM (ClickUp/HubSpot/Salesforce/etc.)
```

### How It Works
1. **Beyond Presence Managed Agent** handles the avatar conversation with built-in LLM
2. **Webhooks** send call events (start, end, transcript) to n8n in real-time
3. **n8n workflows** process the data and interact with your CRM via API
4. **Optional: Custom LLM endpoint** in n8n can provide dynamic responses back to the avatar

### Key Features
- ✅ **Zero infrastructure** - Beyond Presence handles avatar hosting, scaling, LLM
- ✅ **Visual workflow builder** - n8n provides drag-and-drop automation
- ✅ **Pre-built integrations** - 1000+ apps including most CRMs
- ✅ **Real-time webhooks** - Process call events as they happen
- ✅ **Call transcripts** - Full conversation history for CRM logging

### Limitations
- ⚠️ **Async only** - Avatar can't wait for CRM response during conversation
- ⚠️ **No real-time tool calling** - CRM updates happen after conversation ends
- ⚠️ **No call transfer control** - Beyond Presence Managed Agents don't support SIP transfer

### Best For
- Post-call CRM automation (logging calls, creating leads, sending follow-ups)
- Call analytics and reporting
- Batch processing of conversation data
- Simple integrations without real-time requirements

### Implementation Steps

#### 1. Set Up Beyond Presence Managed Agent
```bash
# Create agent via Dashboard (https://app.bey.chat)
# Or via API:
curl -X POST "https://api.bey.dev/v1/agents" \
  -H "x-api-key: sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CRM Assistant",
    "avatar_id": "your-avatar-id",
    "system_prompt": "You are a helpful CRM assistant. Gather customer information including name, email, phone, and inquiry details.",
    "llm_provider": "openai",
    "llm_model": "gpt-4"
  }'
```

#### 2. Configure Webhooks in Beyond Presence
Go to Settings → Webhooks and add your n8n webhook URL:
- Event: `call.ended` (for post-call processing)
- Event: `call.started` (for real-time notifications)
- URL: `https://your-n8n-instance.com/webhook/beyond-presence`

#### 3. Create n8n Workflow
See `n8n_workflows/beyond_presence_crm_sync.json` for a complete example.

**Workflow nodes:**
1. **Webhook Trigger** - Receives Beyond Presence events
2. **Switch** - Routes based on event type (call.started, call.ended)
3. **HTTP Request** - Fetch full call transcript via Beyond Presence API
4. **AI Agent** - Extract structured data (name, email, phone, inquiry)
5. **CRM Node** - Create/update lead in your CRM
6. **Email Node** - Send notification to sales team

#### 4. Test the Integration
```bash
# Test webhook with sample payload
curl -X POST "https://your-n8n-instance.com/webhook/beyond-presence" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "call.ended",
    "call_id": "test-123",
    "agent_id": "agent-456",
    "duration": 120,
    "transcript": "Customer: Hi, I need help with...",
    "metadata": {}
  }'
```

### Cost Estimate
- **Beyond Presence**: ~$0.10-0.30 per minute (includes avatar + LLM)
- **n8n**: Self-hosted (free) or Cloud ($20-50/month)
- **CRM API**: Varies by provider (usually included in subscription)

---

## 🚀 Option 2: LiveKit + Custom Agent (Advanced, Real-Time)

### Architecture Overview
```
LiveKit SIP Trunk (Phone System)
    ↓ (WebRTC audio)
Your Custom Voice Agent (Python/Node.js)
    ↓ (function calling)
CRM API + Call Transfer Logic
    ↓ (speech-to-video)
Beyond Presence Avatar (Video Stream)
```

### How It Works
1. **LiveKit** handles telephony (SIP trunk, WebRTC, audio routing)
2. **Your custom agent** runs LLM with function calling tools
3. **Tools** interact with CRM in real-time during conversation
4. **Beyond Presence Speech-to-Video** adds avatar video layer
5. **LiveKit SIP API** enables call transfer to human agents

### Key Features
- ✅ **Real-time tool calling** - CRM lookups during conversation
- ✅ **Call transfer** - Route to humans or other numbers via SIP
- ✅ **Full control** - Custom logic, workflows, integrations
- ✅ **Multi-modal** - Voice + video + screen sharing
- ✅ **Low latency** - Sub-second response times

### Limitations
- ⚠️ **Infrastructure required** - You host the agent server
- ⚠️ **More complex** - Requires coding (Python/Node.js)
- ⚠️ **SIP trunk setup** - Need Twilio/Telnyx/etc. account
- ⚠️ **Higher cost** - Separate billing for LiveKit + Beyond Presence + SIP

### Best For
- Real-time CRM interactions (lookup customer during call)
- Call routing and transfer (IVR, directory, escalation)
- Complex workflows (multi-step processes, conditional logic)
- Custom business logic and integrations

### Implementation Steps

#### 1. Set Up LiveKit Cloud
```bash
# Sign up at https://cloud.livekit.io
# Get API credentials (API Key, API Secret, WebSocket URL)
```

#### 2. Configure SIP Trunk
Choose a provider (Twilio, Telnyx, Vonage) and configure:
- **Inbound**: Point to LiveKit SIP endpoint
- **Outbound**: Enable PSTN calling and SIP REFER (for transfers)

#### 3. Build Custom Voice Agent
See `livekit_agent/crm_agent.py` for a complete example.

**Key components:**
```python
from livekit.agents import Agent, function_tool, RunContext
from livekit import api

class CRMAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a CRM assistant. Help customers by looking up their information and routing calls.",
            tools=[
                self.lookup_customer,
                self.create_lead,
                self.transfer_to_sales
            ]
        )
    
    @function_tool()
    async def lookup_customer(self, ctx: RunContext, phone: str) -> dict:
        """Look up customer information by phone number"""
        # Call your CRM API
        customer = await crm_api.get_customer(phone)
        return customer
    
    @function_tool()
    async def create_lead(self, ctx: RunContext, name: str, email: str, phone: str) -> str:
        """Create a new lead in the CRM"""
        lead_id = await crm_api.create_lead(name, email, phone)
        return f"Lead created with ID: {lead_id}"
    
    @function_tool()
    async def transfer_to_sales(self, ctx: RunContext) -> str:
        """Transfer call to sales team"""
        await ctx.session.generate_reply(
            instructions="Inform the customer you're transferring them to sales."
        )
        
        job_ctx = get_job_context()
        await job_ctx.api.sip.transfer_sip_participant(
            api.TransferSIPParticipantRequest(
                room_name=job_ctx.room.name,
                participant_identity=ctx.participant.identity,
                transfer_to="tel:+15105550123"  # Sales team number
            )
        )
        return "Call transferred"
```

#### 4. Add Beyond Presence Avatar
```python
# Install Beyond Presence LiveKit plugin
# pip install beyondpresence-livekit

from beyondpresence import SpeechToVideoPlugin

# Add to your agent
plugin = SpeechToVideoPlugin(
    api_key="sk-your-bey-api-key",
    avatar_id="your-avatar-id"
)

# The plugin converts your agent's audio to avatar video
```

#### 5. Deploy Agent
```bash
# Run locally for testing
python crm_agent.py dev

# Deploy to LiveKit Cloud
livekit-cli deploy crm_agent.py
```

#### 6. Test Call Flow
1. Call your LiveKit phone number
2. Agent answers and greets you
3. Ask: "Look up my account" → Agent calls `lookup_customer` tool
4. Ask: "Transfer me to sales" → Agent calls `transfer_to_sales` tool
5. Call is transferred to human agent

### Cost Estimate
- **LiveKit**: $0.004/min participant + $0.01/min SIP
- **Beyond Presence Speech-to-Video**: ~$0.10-0.20/min
- **SIP Provider**: $0.01-0.02/min (Twilio/Telnyx)
- **LLM**: $0.002-0.02/min (OpenAI/Anthropic)
- **Total**: ~$0.13-0.25/min

---

## 📊 Comparison Matrix

| Feature | Option 1: n8n Backend | Option 2: LiveKit + Custom Agent |
|---------|----------------------|----------------------------------|
| **Complexity** | Low (no-code) | High (requires coding) |
| **Setup Time** | 1-2 hours | 1-2 days |
| **Real-time CRM** | ❌ No | ✅ Yes |
| **Call Transfer** | ❌ No | ✅ Yes |
| **Infrastructure** | ☁️ Managed | 🖥️ Self-hosted |
| **Cost/min** | $0.10-0.30 | $0.13-0.25 |
| **Scalability** | Auto | Manual |
| **Customization** | Limited | Unlimited |
| **Best For** | Post-call automation | Real-time interactions |

---

## 🎯 Recommendation

### Choose **Option 1 (n8n Backend)** if:
- You want quick setup with minimal coding
- Post-call CRM updates are sufficient
- You don't need call transfer functionality
- You prefer managed infrastructure

### Choose **Option 2 (LiveKit + Custom Agent)** if:
- You need real-time CRM lookups during calls
- Call transfer/routing is required
- You want full control over conversation logic
- You have development resources

---

## 📁 Project Structure

```
beyond_presence_crm_integration/
├── README.md                          # This file
├── n8n_workflows/
│   ├── beyond_presence_crm_sync.json  # Option 1: n8n workflow
│   └── workflow_setup_guide.md        # Setup instructions
├── livekit_agent/
│   ├── crm_agent.py                   # Option 2: Custom agent
│   ├── requirements.txt               # Python dependencies
│   ├── config.yaml                    # Configuration
│   └── deployment_guide.md            # Deployment instructions
└── examples/
    ├── crm_integrations/
    │   ├── clickup_example.py         # ClickUp API integration
    │   ├── hubspot_example.py         # HubSpot API integration
    │   └── salesforce_example.py      # Salesforce API integration
    └── call_flows/
        ├── sales_qualification.py     # Sales lead qualification flow
        ├── customer_support.py        # Support ticket creation flow
        └── appointment_booking.py     # Calendar integration flow
```

---

## 🔗 Resources

### Beyond Presence
- [Documentation](https://docs.bey.dev)
- [API Reference](https://docs.bey.dev/api-reference)
- [Dashboard](https://app.bey.chat)
- [n8n Integration](https://n8n.io/integrations/beyond-presence/)

### LiveKit
- [Documentation](https://docs.livekit.io)
- [Agents Guide](https://docs.livekit.io/agents/)
- [Telephony Integration](https://docs.livekit.io/agents/start/telephony/)
- [Function Calling](https://docs.livekit.io/agents/build/tools/)

### n8n
- [Documentation](https://docs.n8n.io)
- [Workflow Templates](https://n8n.io/workflows/)
- [Community Forum](https://community.n8n.io)

---

## 🚦 Next Steps

1. **Review both options** and decide which fits your requirements
2. **Set up accounts** (Beyond Presence, n8n or LiveKit, CRM)
3. **Follow the implementation guide** for your chosen option
4. **Test with sample calls** before going live
5. **Monitor and optimize** based on real usage

Need help? Check the detailed guides in the respective folders or reach out to support.
