# Quick Start Guide - Beyond Presence CRM Integration

Choose your path based on your needs and technical expertise.

---

## 🎯 Which Option Should I Choose?

### Choose Option 1 (n8n Backend) if you want:
- ✅ **Quick setup** (1-2 hours)
- ✅ **No coding required** (visual workflow builder)
- ✅ **Post-call automation** (log calls, create leads, send emails)
- ✅ **Managed infrastructure** (no servers to maintain)
- ✅ **Lower complexity** (easier to maintain)

**Best for:** Sales teams, small businesses, non-technical users

### Choose Option 2 (LiveKit + Custom Agent) if you need:
- ✅ **Real-time CRM lookups** (during the conversation)
- ✅ **Call transfer capability** (route to humans)
- ✅ **Full customization** (unlimited business logic)
- ✅ **Complex workflows** (multi-step processes)
- ✅ **Advanced features** (IVR, voicemail detection, etc.)

**Best for:** Enterprises, developers, complex use cases

---

## 🚀 Quick Start - Option 1 (n8n Backend)

### 5-Minute Setup

1. **Create Beyond Presence Agent**
   ```bash
   # Go to https://app.bey.chat
   # Click "Add New Agent"
   # Choose avatar and configure
   ```

2. **Set Up n8n**
   ```bash
   # Docker (easiest)
   docker run -it --rm -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
   
   # Open http://localhost:5678
   ```

3. **Import Workflow**
   - Download: `n8n_workflows/beyond_presence_crm_sync.json`
   - In n8n: Workflows → Import from File
   - Configure credentials (Beyond Presence, CRM, Email)

4. **Connect Webhook**
   - Copy n8n webhook URL
   - Add to Beyond Presence Settings → Webhooks
   - Test with a call

**Done!** Your avatar now logs calls to your CRM automatically.

### What You Get
- 📞 Automatic call logging
- 📝 AI-powered data extraction
- 📧 Email notifications for hot leads
- 📊 CRM lead creation
- 🔄 Fully customizable workflow

---

## 🚀 Quick Start - Option 2 (LiveKit + Custom Agent)

### 30-Minute Setup

1. **Set Up LiveKit**
   ```bash
   # Sign up at https://cloud.livekit.io
   # Create project and note credentials
   ```

2. **Install Dependencies**
   ```bash
   cd livekit_agent
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Customize CRM Integration**
   ```python
   # Edit crm_agent.py
   # Replace CRMClient with your actual CRM API
   ```

5. **Test Locally**
   ```bash
   python crm_agent.py dev
   ```

6. **Deploy**
   ```bash
   livekit-cli agent deploy crm_agent.py
   ```

**Done!** Your agent can now lookup CRM data in real-time and transfer calls.

### What You Get
- 🔍 Real-time CRM lookups during calls
- 📞 Call transfer to human agents
- 🛠️ Custom tools and business logic
- 🎯 Full conversation control
- 📊 Advanced analytics

---

## 📊 Side-by-Side Comparison

| Feature | Option 1: n8n | Option 2: LiveKit |
|---------|---------------|-------------------|
| **Setup Time** | 1-2 hours | 1-2 days |
| **Coding Required** | None | Python/Node.js |
| **Real-time CRM** | ❌ No | ✅ Yes |
| **Call Transfer** | ❌ No | ✅ Yes |
| **Cost per Minute** | $0.10-0.30 | $0.13-0.25 |
| **Scalability** | Auto | Manual |
| **Maintenance** | Low | Medium |
| **Customization** | Limited | Unlimited |

---

## 💡 Common Use Cases

### Use Case 1: Sales Lead Qualification (Option 1)
**Scenario:** Avatar qualifies leads and creates CRM records

**Flow:**
1. Customer talks to avatar
2. Avatar gathers: name, email, phone, needs
3. Call ends → Webhook fires
4. n8n extracts data with AI
5. Lead created in CRM
6. Sales team notified

**Setup:** 1 hour | **Cost:** ~$0.15/call

---

### Use Case 2: Customer Support with Transfer (Option 2)
**Scenario:** Avatar handles simple issues, transfers complex ones

**Flow:**
1. Customer calls support number
2. Avatar answers and identifies customer
3. Avatar looks up account in CRM (real-time)
4. If simple: Avatar resolves issue
5. If complex: Avatar transfers to human

**Setup:** 2 days | **Cost:** ~$0.20/call

---

### Use Case 3: Order Status Checker (Option 2)
**Scenario:** Customers check order status via phone

**Flow:**
1. Customer calls and provides order number
2. Avatar looks up order in real-time
3. Avatar provides tracking info
4. Avatar offers to email details
5. Call ends automatically

**Setup:** 1 day | **Cost:** ~$0.15/call

---

### Use Case 4: Appointment Booking (Option 1 + Option 2)
**Scenario:** Avatar books appointments and syncs to calendar

**Option 1 (Post-call):**
- Avatar collects preferred date/time
- After call: n8n creates calendar event
- Confirmation email sent

**Option 2 (Real-time):**
- Avatar checks calendar availability live
- Avatar books appointment during call
- Immediate confirmation

---

## 🔧 Customization Examples

### Add Slack Notifications (Option 1)
```javascript
// Add Slack node to n8n workflow
{
  "channel": "#sales-leads",
  "text": "🔥 New lead: {{ $json.customer_name }}\nPhone: {{ $json.customer_phone }}\nInterest: {{ $json.inquiry_type }}"
}
```

### Add Custom Tool (Option 2)
```python
@function_tool()
async def check_inventory(self, ctx: RunContext, product_sku: str) -> dict:
    """Check if product is in stock"""
    inventory = await inventory_api.check(product_sku)
    return {
        "in_stock": inventory["quantity"] > 0,
        "quantity": inventory["quantity"],
        "next_restock": inventory["restock_date"]
    }
```

---

## 📈 Scaling Considerations

### Option 1 (n8n) Scaling
- **10-100 calls/day**: Self-hosted n8n on small VPS ($10/mo)
- **100-1000 calls/day**: n8n Cloud Pro ($50/mo)
- **1000+ calls/day**: n8n Enterprise + load balancing

### Option 2 (LiveKit) Scaling
- **10-100 concurrent calls**: Single agent instance
- **100-500 concurrent calls**: 3-5 agent instances + load balancer
- **500+ concurrent calls**: Auto-scaling Kubernetes cluster

---

## 🎓 Learning Resources

### For Option 1 (n8n)
- [n8n Documentation](https://docs.n8n.io)
- [n8n Academy](https://academy.n8n.io)
- [Community Forum](https://community.n8n.io)
- [Workflow Templates](https://n8n.io/workflows)

### For Option 2 (LiveKit)
- [LiveKit Docs](https://docs.livekit.io)
- [Agents Guide](https://docs.livekit.io/agents/)
- [Python Examples](https://github.com/livekit-examples/python-agents-examples)
- [Discord Community](https://livekit.io/discord)

### Beyond Presence
- [Documentation](https://docs.bey.dev)
- [API Reference](https://docs.bey.dev/api-reference)
- [Examples](https://github.com/bey-dev/bey-examples)

---

## 🆘 Getting Help

### Option 1 Support
- **n8n Issues**: https://community.n8n.io
- **Beyond Presence**: support@beyondpresence.ai
- **This Project**: See `n8n_workflows/workflow_setup_guide.md`

### Option 2 Support
- **LiveKit Issues**: https://livekit.io/discord
- **Beyond Presence**: support@beyondpresence.ai
- **This Project**: See `livekit_agent/deployment_guide.md`

---

## 🎯 Next Steps

1. **Review** the main README.md for detailed architecture
2. **Choose** your option based on requirements
3. **Follow** the setup guide for your chosen option
4. **Test** with sample calls
5. **Deploy** to production
6. **Monitor** and optimize

---

## 💰 Cost Calculator

### Option 1 Monthly Cost (100 calls/day)
- Beyond Presence: 100 calls × 3 min × $0.20 = $60/day = **$1,800/mo**
- n8n Cloud: **$50/mo**
- CRM API: Usually included
- **Total: ~$1,850/mo**

### Option 2 Monthly Cost (100 calls/day)
- LiveKit: 100 calls × 3 min × $0.014 = $4.20/day = **$126/mo**
- Beyond Presence: 100 calls × 3 min × $0.15 = $45/day = **$1,350/mo**
- SIP Provider: 100 calls × 3 min × $0.015 = $4.50/day = **$135/mo**
- LLM (OpenAI): ~**$100/mo**
- **Total: ~$1,711/mo**

*Note: Costs vary based on call duration, features used, and providers chosen.*

---

## ✅ Pre-Launch Checklist

### Before Going Live
- [ ] Test with 10+ sample calls
- [ ] Verify CRM integration works
- [ ] Test error handling (bad data, API failures)
- [ ] Set up monitoring and alerts
- [ ] Configure backup/failover
- [ ] Train team on system
- [ ] Prepare customer support docs
- [ ] Test call transfer (Option 2 only)
- [ ] Verify data privacy compliance
- [ ] Set up analytics tracking

---

Ready to get started? Pick your option and dive into the detailed guides! 🚀
