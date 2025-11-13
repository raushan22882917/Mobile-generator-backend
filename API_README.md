# Real-Time App Generation API

Production-ready API for generating React Native Expo apps with real-time progress updates.

## 🚀 Quick Start

### 1. Start Server
```bash
uvicorn main:app --reload
```

### 2. Generate App (Fast Mode)
```bash
curl -X POST http://localhost:8000/api/v1/fast-generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a todo list app",
    "user_id": "user123"
  }'
```

### 3. Connect WebSocket for Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/generate/PROJECT_ID');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`${msg.data.progress}%: ${msg.data.message}`);
  
  if (msg.data.preview_url) {
    console.log('Preview ready:', msg.data.preview_url);
  }
};
```

## 📡 API Endpoints

### Fast Generate (Recommended)
```
POST /api/v1/fast-generate
```
Returns immediately, processes in background.

### WebSocket Updates
```
WS /api/v1/ws/generate/{project_id}
```
Real-time progress updates.

### Legacy Generate
```
POST /generate
```
Waits for completion (slower).

### Project Status
```
GET /status/{project_id}
```

### List Projects
```
GET /projects
```

## 📊 Progress Flow

```
5%   - Analyzing
15%  - Creating project
25%  - Generating base
35%  - Installing dependencies
45%  - Starting server
55%  - Creating tunnel
60%  - ✅ PREVIEW READY!
85%  - Adding screens
90%  - Adding components
100% - Complete!
```

## 🎯 Features

- ⚡ **Fast Mode** - Preview in 45 seconds
- 📡 **Real-time Updates** - WebSocket streaming
- 🔄 **Progressive** - Screens added live
- 📱 **Mobile Preview** - QR code + ngrok tunnel
- 🎨 **Templates** - Pre-made UI themes
- 💾 **Download** - Export as ZIP

## 📚 Documentation

- **API_DOCUMENTATION.md** - Complete API reference
- **STREAMING_ARCHITECTURE.md** - Technical details
- **QUICK_START_STREAMING.md** - Quick guide

## 🔧 Configuration

Create `.env` file:
```env
OPENAI_API_KEY=your_key
NGROK_AUTH_TOKEN=your_token
API_KEY=your_api_key
REQUIRE_API_KEY=false
```

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Generate test app
curl -X POST http://localhost:8000/api/v1/fast-generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Create a simple app","user_id":"test"}'
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Time to preview | 45 seconds |
| Total time | 100 seconds |
| Concurrent users | 10+ |
| API cost per app | $0.42 |

## 🔒 Security

- API key authentication
- Rate limiting (10 req/min)
- Input sanitization
- CORS configuration

## 💡 Example Integration

```javascript
// Your frontend code
async function generateApp(prompt) {
  // 1. Start generation
  const res = await fetch('http://localhost:8000/api/v1/fast-generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, user_id: 'user123' })
  });
  
  const { project_id, websocket_url } = await res.json();
  
  // 2. Connect WebSocket
  const ws = new WebSocket(`ws://localhost:8000${websocket_url}`);
  
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    // Update UI
    updateProgress(msg.data.progress);
    
    // Show preview when ready
    if (msg.data.preview_url) {
      showPreview(msg.data.preview_url);
    }
    
    // Handle completion
    if (msg.type === 'complete') {
      showSuccess(msg.data);
    }
  };
  
  return project_id;
}
```

## 🚦 Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `429` - Rate Limit
- `503` - Service Unavailable

## 📞 Support

- Documentation: See markdown files
- Logs: `uvicorn main:app --log-level debug`
- Issues: Check error messages

## 🎉 Ready to Use!

The API is production-ready and optimized for your frontend integration.

---

**Version:** 1.0.0  
**License:** MIT
