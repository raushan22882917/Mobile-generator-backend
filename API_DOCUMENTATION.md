# API Documentation - Real-Time App Generation

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require API key authentication (if enabled in config).

```http
X-API-Key: your-api-key-here
```

---

## Endpoints

### 1. Fast Generate (Recommended)
**POST** `/api/v1/fast-generate`

Returns immediately and processes in background. Use WebSocket for updates.

#### Request
```json
{
  "prompt": "Create a todo list app with CRUD operations",
  "user_id": "user123",
  "template_id": "modern-blue"
}
```

#### Response (Immediate)
```json
{
  "project_id": "abc-123-def-456",
  "status": "processing",
  "message": "Generation started. Connect to WebSocket for updates.",
  "websocket_url": "/api/v1/ws/generate/abc-123-def-456"
}
```

#### Usage
```javascript
// 1. Call fast-generate
const response = await fetch('http://localhost:8000/api/v1/fast-generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-key'
  },
  body: JSON.stringify({
    prompt: 'Create a todo app',
    user_id: 'user123'
  })
});

const { project_id, websocket_url } = await response.json();

// 2. Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000${websocket_url}`);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.data.progress + '%: ' + msg.data.message);
  
  if (msg.data.preview_url) {
    console.log('Preview ready:', msg.data.preview_url);
  }
};
```

---

### 2. WebSocket Generate
**WebSocket** `/api/v1/ws/generate/{project_id}`

Real-time bidirectional communication.

#### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/generate/project-123');
```

#### Send Start Signal
```json
{
  "action": "start",
  "prompt": "Create a fitness tracking app",
  "user_id": "user123",
  "template_id": "modern-blue",
  "fast_mode": false
}
```

#### Receive Progress Updates
```json
{
  "type": "progress",
  "data": {
    "stage": "preview_ready",
    "message": "Preview ready! Scan QR code...",
    "progress": 60,
    "preview_url": "https://abc.ngrok.io",
    "screens_added": ["Home", "Profile"]
  }
}
```

#### Receive Completion
```json
{
  "type": "complete",
  "data": {
    "success": true,
    "project_id": "abc-123",
    "preview_url": "https://abc.ngrok.io",
    "screens_added": ["Home", "Profile", "Settings"],
    "app_name": "fitness-app-x7k2"
  }
}
```

#### Receive Error
```json
{
  "type": "error",
  "error": "Failed to install dependencies"
}
```

---

### 3. Legacy Generate (Slower)
**POST** `/generate`

Original endpoint - waits for completion before returning.

#### Request
```json
{
  "prompt": "Create a todo list app",
  "user_id": "user123",
  "template_id": "modern-blue"
}
```

#### Response (After ~100 seconds)
```json
{
  "project_id": "abc-123",
  "preview_url": "https://abc.ngrok.io",
  "status": "success",
  "message": "App generated successfully",
  "created_at": "2025-11-13T10:30:00"
}
```

---

### 4. Get Project Status
**GET** `/status/{project_id}`

Check current status of a project.

#### Response
```json
{
  "project_id": "abc-123",
  "status": "ready",
  "preview_url": "https://abc.ngrok.io",
  "error": null,
  "created_at": "2025-11-13T10:30:00",
  "last_active": "2025-11-13T10:32:00"
}
```

#### Status Values
- `initializing` - Creating project
- `generating_code` - Generating code
- `installing_deps` - Installing dependencies
- `starting_server` - Starting Expo server
- `creating_tunnel` - Creating preview tunnel
- `ready` - Preview ready
- `error` - Generation failed

---

### 5. List Projects
**GET** `/projects`

Get all projects.

#### Response
```json
{
  "projects": [
    {
      "id": "abc-123",
      "name": "fitness-app-x7k2",
      "status": "ready",
      "preview_url": "https://abc.ngrok.io",
      "created_at": "2025-11-13T10:30:00",
      "prompt": "Create a fitness tracking app...",
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### 6. Activate Project
**POST** `/projects/{project_id}/activate`

Reactivate an inactive project.

#### Response
```json
{
  "project_id": "abc-123",
  "status": "ready",
  "preview_url": "https://abc.ngrok.io",
  "message": "Project activated successfully"
}
```

---

### 7. Download Project
**GET** `/download/{project_id}`

Download project as ZIP file.

#### Response
Binary ZIP file

---

### 8. Get Project Files
**GET** `/files/{project_id}`

Get project file tree.

#### Response
```json
{
  "project_id": "abc-123",
  "file_tree": [
    {
      "name": "app",
      "type": "folder",
      "path": "app",
      "children": [
        {
          "name": "index.tsx",
          "type": "file",
          "path": "app/index.tsx",
          "content": "import React from 'react'..."
        }
      ]
    }
  ]
}
```

---

### 9. Health Check
**GET** `/health`

Check API health.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T10:30:00",
  "active_projects": 3,
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 35.8
  }
}
```

---

## Progress Stages

### Stage Flow
1. **analyzing** (5%) - Analyzing requirements
2. **creating_project** (15%) - Creating Expo project
3. **generating_base** (25%) - Generating base code
4. **installing_deps** (35%) - Installing dependencies
5. **starting_server** (45%) - Starting dev server
6. **creating_tunnel** (55%) - Creating preview link
7. **preview_ready** (60%) - ✅ Preview is live!
8. **generating_screens** (60-85%) - Adding screens
9. **adding_components** (90%) - Adding components
10. **generating_images** (95%) - Generating images
11. **complete** (100%) - All done!

---

## Error Handling

### Error Response Format
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "details": "Additional details",
  "suggestion": "What to do next"
}
```

### Common Errors

#### 400 Bad Request
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": ["prompt: field required"]
}
```

#### 404 Not Found
```json
{
  "error": "PROJECT_NOT_FOUND",
  "message": "Project abc-123 not found"
}
```

#### 429 Too Many Requests
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later."
}
```

#### 503 Service Unavailable
```json
{
  "error": "RESOURCE_LIMIT",
  "message": "Maximum concurrent projects reached"
}
```

---

## Rate Limiting

- **10 requests per minute** per IP
- Returns `429 Too Many Requests` when exceeded
- Check `X-RateLimit-Remaining` header

---

## CORS

Allowed origins (configurable):
- `http://localhost:3000`
- `http://localhost:3001`
- Your production domain

---

## WebSocket Protocol

### Connection Lifecycle
```
1. Client connects to ws://host/api/v1/ws/generate/{project_id}
2. Server accepts connection
3. Client sends start signal
4. Server sends progress updates
5. Server sends completion/error
6. Connection closes
```

### Message Types
- `progress` - Progress update
- `complete` - Generation complete
- `error` - Error occurred

---

## Best Practices

### 1. Use Fast Generate + WebSocket
```javascript
// Best approach
const res = await fetch('/api/v1/fast-generate', {...});
const { project_id, websocket_url } = await res.json();
const ws = new WebSocket(`ws://localhost:8000${websocket_url}`);
```

### 2. Handle Reconnection
```javascript
let reconnectAttempts = 0;
const maxReconnects = 3;

ws.onclose = () => {
  if (reconnectAttempts < maxReconnects) {
    setTimeout(() => {
      reconnectAttempts++;
      connectWebSocket();
    }, 2000);
  }
};
```

### 3. Show Progress
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  // Update progress bar
  progressBar.style.width = msg.data.progress + '%';
  
  // Show preview when ready
  if (msg.data.preview_url) {
    showPreview(msg.data.preview_url);
  }
};
```

### 4. Handle Errors
```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  showError('Connection failed. Please try again.');
};
```

---

## Example: Complete Integration

```javascript
class AppGenerator {
  constructor(apiUrl) {
    this.apiUrl = apiUrl;
    this.ws = null;
  }
  
  async generate(prompt, onProgress) {
    // 1. Start generation
    const response = await fetch(`${this.apiUrl}/api/v1/fast-generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, user_id: 'user123' })
    });
    
    const { project_id, websocket_url } = await response.json();
    
    // 2. Connect WebSocket
    this.ws = new WebSocket(`ws://localhost:8000${websocket_url}`);
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.type === 'progress') {
        onProgress(msg.data);
      } else if (msg.type === 'complete') {
        console.log('Complete!', msg.data);
        this.ws.close();
      } else if (msg.type === 'error') {
        console.error('Error:', msg.error);
        this.ws.close();
      }
    };
    
    return project_id;
  }
}

// Usage
const generator = new AppGenerator('http://localhost:8000');

generator.generate('Create a todo app', (progress) => {
  console.log(`${progress.progress}%: ${progress.message}`);
  
  if (progress.preview_url) {
    console.log('Preview:', progress.preview_url);
  }
});
```

---

## Testing

### Test with curl
```bash
# Fast generate
curl -X POST http://localhost:8000/api/v1/fast-generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Create a todo app","user_id":"test"}'

# Check status
curl http://localhost:8000/status/abc-123

# Health check
curl http://localhost:8000/health
```

### Test with websocat
```bash
# Install websocat
# brew install websocat  # macOS
# choco install websocat # Windows

# Connect
websocat ws://localhost:8000/api/v1/ws/generate/test-123

# Send (paste this)
{"action":"start","prompt":"Create a todo app","user_id":"test"}
```

---

## Support

For issues or questions:
- Check logs: `uvicorn main:app --log-level debug`
- Review documentation
- Check configuration in `.env`

---

**API Version:** 1.0.0  
**Last Updated:** 2025-11-13
