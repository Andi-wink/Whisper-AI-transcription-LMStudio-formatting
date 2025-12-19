# n8n Workflow Setup Guide - Option 1

This guide walks you through setting up the Beyond Presence + n8n + CRM integration.

---

## Prerequisites

- [ ] Beyond Presence account with API key
- [ ] n8n instance (self-hosted or cloud)
- [ ] CRM account (ClickUp, HubSpot, Salesforce, etc.)
- [ ] SMTP server for email notifications (optional)

---

## Step 1: Set Up Beyond Presence

### 1.1 Create API Key
1. Go to [Beyond Presence Dashboard](https://app.bey.chat)
2. Navigate to **Settings** → **API Keys**
3. Click **Create New Key**
4. Copy and save your API key (starts with `sk-`)

### 1.2 Create Your Agent
```bash
# Option A: Via Dashboard
# Go to https://app.bey.chat/myAgents
# Click "Add New Agent"
# Configure:
#   - Name: "CRM Assistant"
#   - Avatar: Choose or upload custom avatar
#   - System Prompt: See below
#   - LLM: GPT-4 or Claude
#   - Voice: Choose preferred voice

# Option B: Via API
curl -X POST "https://api.bey.dev/v1/agents" \
  -H "x-api-key: sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CRM Assistant",
    "avatar_id": "your-avatar-id",
    "system_prompt": "You are a professional customer service representative. Your goal is to:\n1. Greet customers warmly\n2. Gather their contact information (name, email, phone)\n3. Understand their inquiry or needs\n4. Provide helpful information\n5. Confirm next steps\n\nBe conversational, empathetic, and professional. Always confirm spelling of names and email addresses.",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "voice_provider": "elevenlabs",
    "voice_id": "your-voice-id"
  }'
```

### 1.3 Get Your Agent URL
After creation, you'll receive:
- **Agent ID**: `agent-abc123`
- **Conversation URL**: `https://bey.chat/agent-abc123`
- **Embed Code**: For website integration

---

## Step 2: Set Up n8n

### 2.1 Install n8n
```bash
# Option A: Docker (Recommended)
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Option B: npm
npm install n8n -g
n8n start

# Option C: n8n Cloud
# Sign up at https://n8n.io/cloud
```

### 2.2 Install Beyond Presence Node
1. Go to **Settings** → **Community Nodes**
2. Search for "Beyond Presence"
3. Click **Install**
4. Wait for installation to complete

### 2.3 Configure Credentials

#### Beyond Presence API
1. Go to **Credentials** → **Add Credential**
2. Search for "Beyond Presence API"
3. Enter your API key from Step 1.1
4. Test connection
5. Save as "Beyond Presence API"

#### ClickUp API (or your CRM)
1. Go to **Credentials** → **Add Credential**
2. Search for "ClickUp API"
3. Get API token from ClickUp:
   - Go to ClickUp Settings → Apps
   - Generate API Token
4. Enter token in n8n
5. Save as "ClickUp API"

#### SMTP (for email notifications)
1. Go to **Credentials** → **Add Credential**
2. Search for "SMTP"
3. Enter your email server details:
   - Host: smtp.gmail.com (for Gmail)
   - Port: 587
   - User: your-email@gmail.com
   - Password: app-specific password
4. Save as "SMTP"

---

## Step 3: Import Workflow

### 3.1 Import JSON
1. In n8n, click **Workflows** → **Import from File**
2. Select `beyond_presence_crm_sync.json`
3. Click **Import**

### 3.2 Configure Environment Variables
Add these variables in n8n Settings → Variables:

```bash
CLICKUP_LIST_ID=901513394496          # Your ClickUp list ID
NOTIFICATION_EMAIL=noreply@yourcompany.com
SALES_TEAM_EMAIL=sales@yourcompany.com
```

To find your ClickUp List ID:
1. Go to your ClickUp list
2. Look at the URL: `https://app.clickup.com/12345678/v/li/901513394496`
3. The number after `/li/` is your List ID

### 3.3 Update Credentials
For each node in the workflow:
1. Click the node
2. Select the appropriate credential from dropdown
3. Save

---

## Step 4: Configure Webhooks

### 4.1 Get n8n Webhook URL
1. Open the imported workflow
2. Click the **Webhook Trigger** node
3. Copy the **Production URL**
   - Example: `https://your-n8n.com/webhook/beyond-presence-webhook`

### 4.2 Add Webhook to Beyond Presence
1. Go to [Beyond Presence Settings](https://app.bey.chat/settings)
2. Navigate to **Webhooks**
3. Click **Add Webhook**
4. Configure:
   - **URL**: Paste your n8n webhook URL
   - **Events**: Select both:
     - ✅ `call.started`
     - ✅ `call.ended`
   - **Secret**: (optional) for webhook verification
5. Click **Save**

### 4.3 Test Webhook
Beyond Presence will automatically send a test payload. Check n8n executions to verify it was received.

---

## Step 5: Customize Workflow

### 5.1 Modify Data Extraction
Edit the **Extract Customer Data** node to match your needs:

```javascript
// Current extraction prompt
Extract the following information from this call transcript:

{{ $json.transcript }}

Extract:
- customer_name: Full name of the customer
- customer_email: Email address
- customer_phone: Phone number
- inquiry_type: Type of inquiry (sales, support, general)
- inquiry_details: Brief summary of what they need
- sentiment: Overall sentiment (positive, neutral, negative)
- follow_up_required: true/false if follow-up is needed

Return as JSON.
```

Add more fields as needed:
- `company_name`
- `budget_range`
- `timeline`
- `pain_points`
- `competitor_mentions`

### 5.2 Customize CRM Fields
Edit the **Create CRM Lead** node to map to your CRM fields:

```javascript
// ClickUp custom fields mapping
{
  'customer_name': $json.customer_name,
  'customer_email': $json.customer_email,
  'customer_phone': $json.customer_phone,
  'inquiry_type': $json.inquiry_type,
  'inquiry_details': $json.inquiry_details,
  'sentiment': $json.sentiment,
  'call_duration': $('Fetch Call Transcript').item.json.duration,
  'call_transcript': $('Fetch Call Transcript').item.json.transcript,
  'call_date': $now.toISO()
}
```

### 5.3 Add Additional Actions
Common additions:

**Send SMS Notification:**
```javascript
// Add Twilio node after "Create CRM Lead"
{
  "to": $json.customer_phone,
  "from": "+15105550123",
  "body": "Thank you for contacting us! We've received your inquiry and will follow up within 24 hours."
}
```

**Create Calendar Event:**
```javascript
// Add Google Calendar node
{
  "summary": "Follow up with {{ $json.customer_name }}",
  "start": "{{ $now.plus({ days: 1 }).toISO() }}",
  "end": "{{ $now.plus({ days: 1, hours: 1 }).toISO() }}",
  "description": "{{ $json.inquiry_details }}"
}
```

**Slack Notification:**
```javascript
// Add Slack node
{
  "channel": "#sales-leads",
  "text": "🔥 New hot lead from Beyond Presence!\n\n*Name:* {{ $json.customer_name }}\n*Phone:* {{ $json.customer_phone }}\n*Inquiry:* {{ $json.inquiry_type }}\n\n<{{ $('Create CRM Lead').item.json.url }}|View in CRM>"
}
```

---

## Step 6: Test End-to-End

### 6.1 Activate Workflow
1. In n8n, click **Active** toggle (top right)
2. Workflow is now listening for webhooks

### 6.2 Test Call
1. Go to your Beyond Presence agent URL
2. Start a conversation
3. Provide test information:
   - Name: "John Doe"
   - Email: "john@example.com"
   - Phone: "+1-510-555-0123"
   - Inquiry: "I'm interested in your product pricing"
4. End the call

### 6.3 Verify Results
Check that:
- [ ] n8n execution completed successfully
- [ ] Lead was created in CRM
- [ ] Email notification was sent (if follow-up required)
- [ ] All data was extracted correctly

### 6.4 Review Execution
1. Go to n8n **Executions**
2. Click the latest execution
3. Review each node's output
4. Check for any errors

---

## Step 7: Monitor and Optimize

### 7.1 Set Up Error Notifications
Add error handling to the workflow:

1. Add **Error Trigger** node
2. Connect to **Send Email** node
3. Configure alert email

### 7.2 Monitor Webhook Deliveries
In Beyond Presence dashboard:
1. Go to **Settings** → **Webhooks**
2. Click on your webhook
3. View **Recent Deliveries**
4. Check for failed deliveries

### 7.3 Optimize Data Extraction
After 10-20 test calls:
1. Review extraction accuracy
2. Adjust AI prompt if needed
3. Add validation rules
4. Handle edge cases

---

## Troubleshooting

### Webhook Not Receiving Data
- ✅ Check webhook URL is correct
- ✅ Verify workflow is active
- ✅ Check n8n is accessible from internet
- ✅ Review Beyond Presence webhook logs

### Data Extraction Errors
- ✅ Check transcript is not empty
- ✅ Verify AI model is responding
- ✅ Test with simpler extraction prompt
- ✅ Add error handling for missing fields

### CRM Creation Fails
- ✅ Verify API credentials are valid
- ✅ Check required fields are provided
- ✅ Ensure field types match (string, number, etc.)
- ✅ Review CRM API rate limits

### Email Not Sending
- ✅ Verify SMTP credentials
- ✅ Check spam folder
- ✅ Test SMTP connection separately
- ✅ Review email server logs

---

## Advanced Configuration

### Custom LLM Endpoint
To use your own LLM for dynamic responses:

```python
# Create custom endpoint in n8n
@app.route('/custom-llm', methods=['POST'])
def custom_llm():
    data = request.json
    conversation_history = data['messages']
    
    # Add custom logic
    customer_data = lookup_crm(data['customer_phone'])
    
    # Generate personalized response
    response = generate_response(conversation_history, customer_data)
    
    return jsonify({'response': response})
```

Then configure in Beyond Presence agent:
```json
{
  "llm_provider": "custom",
  "llm_endpoint": "https://your-n8n.com/webhook/custom-llm"
}
```

### Multi-Language Support
Beyond Presence supports 29 languages. Configure in agent settings:

```json
{
  "language": "auto",  // Auto-detect
  "supported_languages": ["en", "es", "fr", "de"]
}
```

### Call Recording Storage
Store recordings in cloud storage:

1. Add **AWS S3** or **Google Drive** node
2. Upload call recording after transcript
3. Store URL in CRM

---

## Cost Optimization

### Reduce Beyond Presence Costs
- Use shorter system prompts
- Enable silence detection
- Set max call duration
- Use cheaper LLM models for simple tasks

### Reduce n8n Costs
- Self-host instead of cloud
- Batch process calls (vs real-time)
- Use caching for repeated lookups
- Optimize workflow execution

### Reduce CRM API Costs
- Batch create/update operations
- Use webhooks instead of polling
- Cache frequently accessed data
- Implement rate limiting

---

## Next Steps

1. **Scale Testing**: Test with 50-100 calls
2. **Add Analytics**: Track conversion rates, call duration, sentiment
3. **A/B Testing**: Test different agent prompts and voices
4. **Integration**: Connect to more systems (calendar, billing, etc.)
5. **Automation**: Add follow-up sequences and nurture campaigns

---

## Support Resources

- **Beyond Presence**: support@beyondpresence.ai
- **n8n Community**: https://community.n8n.io
- **Documentation**: See main README.md
