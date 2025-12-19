# Architecture Diagrams

Visual representations of both integration options.

---

## Option 1: n8n Backend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CUSTOMER                                 │
│                            ↓                                     │
│                    (Web Browser/Phone)                           │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BEYOND PRESENCE                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Managed Agent (Hosted by Beyond Presence)             │     │
│  │  • Avatar Video Rendering                              │     │
│  │  • LLM (GPT-4/Claude)                                  │     │
│  │  • Speech-to-Text                                      │     │
│  │  • Text-to-Speech                                      │     │
│  │  • Conversation Management                             │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    (Webhook Events)
                    • call.started
                    • call.ended
                    • call.transcript
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         n8n WORKFLOWS                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  1. Webhook Trigger                                    │     │
│  │     ↓                                                  │     │
│  │  2. Event Router (Switch)                             │     │
│  │     ↓                                                  │     │
│  │  3. Fetch Full Transcript (HTTP Request)              │     │
│  │     ↓                                                  │     │
│  │  4. AI Data Extraction (LangChain)                    │     │
│  │     • Extract name, email, phone                      │     │
│  │     • Identify inquiry type                           │     │
│  │     • Analyze sentiment                               │     │
│  │     ↓                                                  │     │
│  │  5. CRM Integration                                   │     │
│  │     • Create/Update Lead                              │     │
│  │     • Log Call Notes                                  │     │
│  │     • Update Custom Fields                            │     │
│  │     ↓                                                  │     │
│  │  6. Conditional Logic                                 │     │
│  │     • If hot lead → Notify sales                      │     │
│  │     • If support → Create ticket                      │     │
│  │     ↓                                                  │     │
│  │  7. Notifications                                     │     │
│  │     • Email to sales team                             │     │
│  │     • Slack message                                   │     │
│  │     • SMS to customer                                 │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CRM SYSTEMS                                 │
│  • ClickUp         • HubSpot        • Salesforce                │
│  • Pipedrive       • Zoho CRM       • Custom CRM                │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow:
1. Customer interacts with avatar
2. Beyond Presence handles conversation
3. Call ends → Webhook fires to n8n
4. n8n fetches transcript and processes data
5. AI extracts structured information
6. CRM record created/updated
7. Notifications sent to team

### Key Characteristics:
- ✅ **Async Processing**: Data processed after call ends
- ✅ **No Infrastructure**: Everything is managed
- ✅ **Visual Workflows**: Drag-and-drop configuration
- ❌ **No Real-time**: Cannot lookup CRM during call
- ❌ **No Transfer**: Cannot route calls to humans

---

## Option 2: LiveKit + Custom Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CUSTOMER                                 │
│                            ↓                                     │
│                    (Phone Call via SIP)                          │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SIP TRUNK PROVIDER                             │
│  • Twilio          • Telnyx         • Vonage                    │
│  • Phone Number Management                                      │
│  • PSTN Connectivity                                            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    (WebRTC Audio Stream)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LIVEKIT SERVER                              │
│  • SIP Gateway                                                  │
│  • WebRTC Infrastructure                                        │
│  • Audio Routing                                                │
│  • Room Management                                              │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    (Audio Track)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              YOUR CUSTOM VOICE AGENT (Python/Node.js)            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Voice Pipeline:                                       │     │
│  │  1. Speech-to-Text (Deepgram/AssemblyAI)              │     │
│  │     ↓                                                  │     │
│  │  2. LLM with Function Calling (OpenAI/Anthropic)      │     │
│  │     ↓                                                  │     │
│  │  3. Tool Execution (Real-time)                        │     │
│  │     ├─→ lookup_customer()                             │     │
│  │     ├─→ check_order_status()                          │     │
│  │     ├─→ create_lead()                                 │     │
│  │     ├─→ transfer_to_sales()                           │     │
│  │     └─→ end_call()                                    │     │
│  │     ↓                                                  │     │
│  │  4. Text-to-Speech (ElevenLabs)                       │     │
│  │     ↓                                                  │     │
│  │  5. Audio Output                                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Beyond Presence Speech-to-Video Plugin                │     │
│  │  • Converts audio to avatar video                     │     │
│  │  • Lip-sync and facial expressions                    │     │
│  │  • Real-time video stream                             │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    (API Calls During Call)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CRM SYSTEMS                                 │
│  • Real-time customer lookup                                    │
│  • Order status checks                                          │
│  • Lead creation                                                │
│  • Note updates                                                 │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    (SIP Transfer if needed)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      HUMAN AGENTS                                │
│  • Sales Team          • Support Team       • Specialists       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow:
1. Customer calls phone number
2. SIP trunk routes to LiveKit
3. LiveKit creates room and invites agent
4. Agent processes audio in real-time
5. LLM decides to call tools (CRM lookup, transfer, etc.)
6. Tools execute and return results
7. Agent responds with updated information
8. Beyond Presence adds avatar video layer
9. If needed, call transferred to human

### Key Characteristics:
- ✅ **Real-time**: CRM lookups during conversation
- ✅ **Call Transfer**: Route to humans via SIP
- ✅ **Full Control**: Custom business logic
- ✅ **Multi-modal**: Voice + Video
- ❌ **Complex**: Requires coding and infrastructure
- ❌ **Maintenance**: Need to manage servers

---

## Comparison: Request Flow

### Option 1 - Post-Call Processing
```
Customer → Avatar → [Call Ends] → Webhook → n8n → CRM
                                   (Async)
```

### Option 2 - Real-Time Processing
```
Customer → SIP → LiveKit → Agent → CRM API → Agent → Customer
                           ↓                    ↑
                        [During Call]      [Immediate Response]
```

---

## Tool Calling Flow (Option 2)

```
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER: "Can you look up my account? My phone is 555-0123"   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Speech-to-Text                                          │
│  Transcription: "Can you look up my account..."                 │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  LLM: Analyzes request and decides to call tool                 │
│  Function Call: lookup_customer(phone="+1-555-0123")            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  TOOL EXECUTION: lookup_customer()                              │
│  1. Validate phone number format                                │
│  2. Call CRM API: GET /customers?phone=+1-555-0123              │
│  3. Parse response                                              │
│  4. Return structured data                                      │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  CRM RESPONSE:                                                  │
│  {                                                              │
│    "found": true,                                               │
│    "name": "John Doe",                                          │
│    "email": "john@example.com",                                 │
│    "status": "active",                                          │
│    "orders": 5,                                                 │
│    "lifetime_value": 2500                                       │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  LLM: Generates natural response with data                      │
│  "I found your account, John! I can see you're a valued         │
│   customer with 5 orders. How can I help you today?"            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Text-to-Speech + Avatar Video                           │
│  Customer hears and sees avatar speaking                        │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    [Conversation continues...]
```

**Total Time:** ~2-3 seconds from request to response

---

## Call Transfer Flow (Option 2)

```
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER: "This is too complex, I need to speak to someone"    │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  LLM: Recognizes transfer request                               │
│  Function Call: transfer_to_sales()                             │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Generates transition message                            │
│  "I understand. Let me connect you with a specialist who        │
│   can help you better. Please hold for just a moment."          │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    [Wait for speech to complete]
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  TOOL: transfer_to_sales()                                      │
│  1. Get sales team phone number from config                     │
│  2. Call LiveKit SIP API: transfer_sip_participant()            │
│  3. Initiate SIP REFER to +1-510-555-0123                       │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  LIVEKIT: Executes SIP transfer                                 │
│  • Sends SIP REFER message                                      │
│  • Connects customer to sales number                            │
│  • Agent session ends                                           │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN AGENT: Answers call                                      │
│  • Receives customer call                                       │
│  • Has access to call history/notes                             │
│  • Continues conversation                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architectures

### Option 1: Fully Managed
```
┌──────────────────────┐
│  Beyond Presence     │ ← Managed by Beyond Presence
│  (Cloud)             │
└──────────────────────┘
          ↓
┌──────────────────────┐
│  n8n Cloud           │ ← Managed by n8n
│  (Cloud)             │
└──────────────────────┘
          ↓
┌──────────────────────┐
│  Your CRM            │ ← Your existing system
│  (Cloud)             │
└──────────────────────┘
```

### Option 2: Hybrid (Recommended)
```
┌──────────────────────┐
│  SIP Provider        │ ← Managed (Twilio/Telnyx)
│  (Cloud)             │
└──────────────────────┘
          ↓
┌──────────────────────┐
│  LiveKit Cloud       │ ← Managed by LiveKit
│  (Cloud)             │
└──────────────────────┘
          ↓
┌──────────────────────┐
│  Your Agent          │ ← You deploy (Docker/K8s)
│  (Your Infrastructure)│
└──────────────────────┘
          ↓
┌──────────────────────┐
│  Beyond Presence     │ ← Managed by Beyond Presence
│  (Cloud)             │
└──────────────────────┘
          ↓
┌──────────────────────┐
│  Your CRM            │ ← Your existing system
│  (Cloud)             │
└──────────────────────┘
```

---

## Security Architecture

### Both Options Include:

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                             │
│                                                                  │
│  1. Transport Layer                                             │
│     • HTTPS/WSS encryption (TLS 1.3)                            │
│     • Certificate validation                                    │
│                                                                  │
│  2. Authentication                                              │
│     • API key authentication                                    │
│     • JWT tokens for sessions                                   │
│     • Webhook signature verification                            │
│                                                                  │
│  3. Authorization                                               │
│     • Role-based access control                                 │
│     • Scope-limited API keys                                    │
│     • IP whitelisting (optional)                                │
│                                                                  │
│  4. Data Protection                                             │
│     • Encryption at rest                                        │
│     • PII data masking                                          │
│     • Audit logging                                             │
│                                                                  │
│  5. Compliance                                                  │
│     • GDPR ready                                                │
│     • HIPAA compatible (with BAA)                               │
│     • SOC 2 Type II                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                      MONITORING STACK                            │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │   Metrics      │  │   Logs         │  │   Traces       │    │
│  │   (Prometheus) │  │   (Loki)       │  │   (Jaeger)     │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│           ↓                  ↓                    ↓             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Grafana Dashboards                          │  │
│  │  • Call volume and duration                              │  │
│  │  • CRM API latency                                       │  │
│  │  • Error rates                                           │  │
│  │  • Customer satisfaction                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Alerting (PagerDuty/Slack)                  │  │
│  │  • High error rate → Alert ops team                      │  │
│  │  • CRM API down → Alert dev team                         │  │
│  │  • High call volume → Scale up                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

These diagrams provide a visual understanding of how both options work. Refer to the detailed documentation for implementation specifics.
