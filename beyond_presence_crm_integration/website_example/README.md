# Website Integration Example

Complete working example of integrating LiveKit with your website to display the Beyond Presence avatar with CRM tools.

---

## 📁 Files

- **index.html** - Main website page with avatar interface
- **styles.css** - Modern, responsive styling
- **app.js** - LiveKit client integration and UI logic
- **token_server.py** - Backend server for generating LiveKit tokens
- **requirements.txt** - Python dependencies for token server

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Token server dependencies
pip install fastapi uvicorn livekit python-dotenv

# Or use requirements file
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxx
```

### Step 3: Start Token Server

```bash
python token_server.py
```

You should see:
```
============================================================
LiveKit Token Server
============================================================
LiveKit URL: wss://your-project.livekit.cloud
API Key configured: True
============================================================

Starting server on http://0.0.0.0:3000
Token endpoint: http://localhost:3000/api/get-token
============================================================
```

### Step 4: Update Website Configuration

Edit `index.html` line ~90:

```javascript
const CONFIG = {
  tokenEndpoint: 'http://localhost:3000/api/get-token',
  // For production: 'https://your-token-server.com/api/get-token'
};
```

### Step 5: Serve Website

**Option A: Python HTTP Server**
```bash
python -m http.server 8000
```

**Option B: Node.js HTTP Server**
```bash
npx http-server -p 8000
```

**Option C: VS Code Live Server**
- Install "Live Server" extension
- Right-click `index.html` → "Open with Live Server"

### Step 6: Test

1. Open http://localhost:8000 in your browser
2. Click "Start Conversation"
3. Allow microphone access
4. Wait for avatar to appear
5. Start talking!

---

## 🔧 Configuration

### Update Token Endpoint

For production deployment:

```javascript
// In index.html
const CONFIG = {
  tokenEndpoint: 'https://your-api.railway.app/api/get-token'
};
```

### Update CORS Settings

In `token_server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-website.com",  # Your actual domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚢 Deployment

### Deploy Token Server

**Option 1: Railway**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# Get URL: https://your-app.railway.app
```

**Option 2: Render**
```bash
# 1. Push code to GitHub
# 2. Connect to Render.com
# 3. Create new Web Service
# 4. Set environment variables
# 5. Deploy
```

**Option 3: Heroku**
```bash
# Create Procfile
echo "web: uvicorn token_server:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create your-token-server
git push heroku main
heroku config:set LIVEKIT_URL=wss://...
heroku config:set LIVEKIT_API_KEY=...
heroku config:set LIVEKIT_API_SECRET=...
```

### Deploy Website

**Option 1: Netlify**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod

# Or drag & drop folder to netlify.com
```

**Option 2: Vercel**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**Option 3: GitHub Pages**
```bash
# 1. Push to GitHub
# 2. Go to Settings → Pages
# 3. Select branch and folder
# 4. Save
```

---

## 🧪 Testing

### Test Token Generation

```bash
curl http://localhost:3000/api/get-token
```

Expected response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "url": "wss://your-project.livekit.cloud",
  "room_name": "demo-1234567890-abc123",
  "participant_identity": "user-xyz789"
}
```

### Test Website Locally

1. Open browser console (F12)
2. Click "Start Conversation"
3. Check for errors in console
4. Verify WebSocket connection
5. Check microphone permissions

### Common Issues

**Token server not responding:**
```bash
# Check if server is running
curl http://localhost:3000/health

# Check logs
# Look for errors in terminal
```

**CORS errors:**
```javascript
// In browser console:
// Access to fetch at '...' from origin '...' has been blocked by CORS

// Fix: Update CORS settings in token_server.py
```

**Microphone not working:**
```javascript
// Check browser permissions
// Chrome: Settings → Privacy → Site Settings → Microphone
// Firefox: Preferences → Privacy → Permissions → Microphone
```

**Avatar video not appearing:**
```bash
# Check agent is running
livekit-cli agent list

# Check agent logs
livekit-cli agent logs website-crm-agent

# Verify Beyond Presence integration
```

---

## 🎨 Customization

### Change Colors

In `styles.css`:

```css
/* Primary color (buttons, accents) */
--primary-color: #4CAF50;  /* Change to your brand color */

/* Background gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
/* Change to your brand gradient */
```

### Change Layout

In `index.html`:

```html
<!-- Adjust avatar container size -->
<div id="avatar-container" style="max-width: 1024px;">
  <!-- Larger avatar -->
</div>
```

### Add Logo

```html
<header>
  <img src="logo.png" alt="Logo" style="height: 40px; margin-bottom: 10px;">
  <h1>AI Avatar Assistant</h1>
</header>
```

### Custom Welcome Message

In `index.html`:

```html
<div class="welcome-content">
  <h2>Welcome to Our AI Assistant</h2>
  <p>Get instant help with your questions</p>
</div>
```

---

## 📊 Analytics

### Track Conversations

Add to `app.js`:

```javascript
// In startConversation()
gtag('event', 'conversation_started', {
  'event_category': 'engagement',
  'event_label': 'avatar_chat'
});

// In endConversation()
gtag('event', 'conversation_ended', {
  'event_category': 'engagement',
  'event_label': 'avatar_chat',
  'value': conversationDuration
});
```

### Monitor Performance

```javascript
// Track connection time
const startTime = Date.now();

// After connection
const connectionTime = Date.now() - startTime;
console.log('Connection time:', connectionTime, 'ms');

// Send to analytics
gtag('event', 'timing_complete', {
  'name': 'avatar_connection',
  'value': connectionTime,
  'event_category': 'performance'
});
```

---

## 🔒 Security

### Production Checklist

- [ ] Use HTTPS for website
- [ ] Use HTTPS for token server
- [ ] Restrict CORS to your domain only
- [ ] Set short token expiration (1 hour)
- [ ] Implement rate limiting on token endpoint
- [ ] Add authentication if needed
- [ ] Monitor for abuse
- [ ] Keep API keys secret (never in frontend code)

### Rate Limiting Example

```python
# In token_server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/get-token")
@limiter.limit("10/minute")  # Max 10 tokens per minute per IP
async def get_token():
    # ... existing code
```

---

## 📱 Mobile Support

The website is fully responsive and works on mobile devices.

### Mobile Testing

1. Open on mobile browser
2. Grant microphone permission
3. Test conversation
4. Check video display
5. Test portrait/landscape

### Mobile Optimizations

Already included:
- ✅ Responsive design
- ✅ Touch-friendly buttons
- ✅ Mobile-optimized video
- ✅ Adaptive layout

---

## 🆘 Troubleshooting

### Problem: "Failed to get token"

**Solution:**
```bash
# Check token server is running
curl http://localhost:3000/health

# Check environment variables
echo $LIVEKIT_API_KEY

# Restart token server
python token_server.py
```

### Problem: "Connection failed"

**Solution:**
```javascript
// Check browser console for specific error
// Common causes:
// 1. Token server not accessible
// 2. CORS issue
// 3. Invalid LiveKit credentials
// 4. Network firewall blocking WebSocket
```

### Problem: "No avatar video"

**Solution:**
```bash
# 1. Check agent is deployed
livekit-cli agent list

# 2. Check agent logs
livekit-cli agent logs website-crm-agent

# 3. Verify Beyond Presence integration in agent code
# 4. Test agent separately
```

### Problem: "Microphone not working"

**Solution:**
```
1. Check browser permissions (chrome://settings/content/microphone)
2. Try different browser
3. Check if microphone works in other apps
4. Look for browser console errors
5. Try HTTPS instead of HTTP (required by some browsers)
```

---

## 📚 Additional Resources

- **LiveKit Docs**: https://docs.livekit.io
- **LiveKit Client SDK**: https://docs.livekit.io/client-sdk-js/
- **Beyond Presence**: https://docs.bey.dev
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🎯 Next Steps

1. ✅ Test locally
2. ✅ Deploy token server
3. ✅ Deploy website
4. ✅ Test production deployment
5. ✅ Add analytics
6. ✅ Monitor performance
7. ✅ Collect user feedback

---

Need help? Check the main integration guide: `livekit_agent/website_integration_guide.md`
