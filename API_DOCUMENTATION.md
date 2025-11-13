# AI Expo App Builder - Complete API Documentation

## Base URL
**Production:** `https://mobile-generator-backend-1098053868371.us-central1.run.app`

## Authentication
Most endpoints require API key authentication via header:
```
X-API-Key: your-api-key-here
```

---

## 📱 Core Generation APIs

### 1. Generate App (Standard)
**POST** `/generate`

Generate a complete Expo app with AI analysis and sequential screen creation.

**Request:**
```json
{
  "prompt": "Create a task management app with priorities",
  "user_id": "user123",
  "template_id": "modern-blue"
}
```

**Response:**
```json
{
  "project_id": "abc123",
  "preview_url": "https://abc123.ngrok.io",
  "status": "success",
  "message": "App generated with 4 screens",
  "created_at": "2024-11-13T10:00:00"
}
```

**Workflow:**
1. AI analyzes prompt → decides app structure
2. Creates Expo project
3. Generates screens sequentially (with detailed logs)
4. Installs dependencies
5. Starts server + creates tunnel
6. Uploads to Cloud Storage

---

### 2. Fast Generate (Background)
**POST** `/api/v1/fast-generate`

Returns immediately, processes in background with WebSocket updates.

**Request:**
```json
{
  "prompt": "Create a weather app",
  "user_id": "user123",
  "template_id": "ocean-blue"
}
```

**Response:**
```json
{
  "project_id": "xyz789",
  "status": "processing",
  "message": "Generation started",
  "websocket_url": "wss://backend.run.app/ws/xyz789"
}
```

**Connect to WebSocket for updates:**
```javascript
const ws = new WebSocket('wss://backend.run.app/ws/xyz789');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update.status, update.message);
};
```

---

### 3. Streaming Generate
**POST** `/api/v1/generate-stream`

Initiate streaming generation with real-time WebSocket updates.

**Request:**
```json
{
  "prompt": "Create a fitness tracker app",
  "user_id": "user123",
  "template_id": "energetic-red",
  "fast_mode": false
}
```

**Response:**
```json
{
  "project_id": "stream123",
  "websocket_url": "wss://backend.run.app/ws/stream/stream123",
  "message": "Connect to WebSocket for updates"
}
```

---

## 📊 Project Management APIs

### 4. List All Projects
**GET** `/projects` or `/api/projects`

Lists projects from local storage AND Cloud Storage.

**Response:**
```json
{
  "projects": [
    {
      "id": "abc123",
      "name": "taskmaster",
      "status": "ready",
      "source": "local",
      "preview_url": "https://abc123.ngrok.io",
      "created_at": "2024-11-13T10:00:00",
      "is_active": true
    },
    {
      "id": "xyz789",
      "name": "weatherapp",
      "status": "archived",
      "source": "cloud_storage",
      "preview_url": null,
      "created_at": "2024-11-12T15:00:00",
      "is_active": false
    }
  ],
  "total": 2,
  "local_count": 1,
  "cloud_count": 1
}
```

---

### 5. Get Project Status
**GET** `/status/{project_id}`

Get detailed project status.

**Response:**
```json
{
  "project_id": "abc123",
  "status": "ready",
  "preview_url": "https://abc123.ngrok.io",
  "error": null,
  "created_at": "2024-11-13T10:00:00",
  "last_active": "2024-11-13T10:30:00"
}
```

**Status Values:**
- `initializing` - Creating project
- `generating_code` - AI generating code
- `installing_deps` - Installing npm packages
- `starting_server` - Starting Expo server
- `creating_tunnel` - Creating ngrok tunnel
- `ready` - App is ready
- `error` - Generation failed
- `archived` - Stored in Cloud Storage

---

### 6. Quick Status Check
**GET** `/quick-status/{project_id}`

Ultra-fast status check for polling.

**Response:**
```json
{
  "status": "ready",
  "port": 8081,
  "url": "https://abc123.ngrok.io",
  "project_id": "abc123"
}
```

---

### 7. Activate Archived Project
**POST** `/projects/{project_id}/activate`

Reactivate a project from Cloud Storage.

**Response:**
```json
{
  "project_id": "abc123",
  "status": "ready",
  "preview_url": "https://new-url.ngrok.io",
  "message": "Project activated successfully"
}
```

**Process:**
1. Downloads from Cloud Storage
2. Installs dependencies
3. Starts Expo server
4. Creates new tunnel

---

### 8. Manual Activate
**POST** `/projects/{project_id}/manual-activate`

Manually activate with custom preview URL.

**Request:**
```json
{
  "preview_url": "https://custom.ngrok.io"
}
```

**Use Case:** When automated activation fails, manually start server and provide URL.

---

## 📦 Cloud Storage APIs

### 9. List Bucket Projects
**GET** `/bucket-projects`

List all projects in Cloud Storage bucket with detailed metadata.

**Response:**
```json
{
  "total_projects": 4,
  "total_size_mb": 125.5,
  "bucket_name": "gen-lang-client-0148980288-ai-expo-builder-archives",
  "projects": [
    {
      "project_id": "abc123",
      "file_name": "abc123.zip",
      "size_mb": 31.2,
      "created_at": "2024-11-13T10:00:00",
      "updated_at": "2024-11-13T10:05:00",
      "gcs_path": "gs://bucket/projects/abc123.zip",
      "download_url": "/download-from-storage/abc123"
    }
  ]
}
```

---

### 10. Download from Cloud Storage
**GET** `/download-from-storage/{project_id}`

Download project ZIP from Cloud Storage.

**Response:** ZIP file download

---

### 11. Download Project (Local)
**GET** `/download/{project_id}`

Download project as ZIP (creates archive from local files).

**Response:** ZIP file download

---

## 📝 File Management APIs

### 12. Get Project Files
**GET** `/files/{project_id}`

Get complete file tree with content.

**Response:**
```json
{
  "project_id": "abc123",
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

### 13. Get File Content
**GET** `/files/{project_id}/{file_path}/content`

Get specific file content.

**Response:**
```json
{
  "content": "import React from 'react'...",
  "path": "app/index.tsx"
}
```

---

### 14. Update File
**PUT** `/files/{project_id}/{file_path}`

Update file content (auto-generates icons/images for screens).

**Request:**
```json
{
  "content": "import React from 'react'..."
}
```

**Response:**
```json
{
  "success": true,
  "path": "app/index.tsx"
}
```

---

### 15. Create File/Folder
**POST** `/files/{project_id}`

Create new file or folder.

**Request:**
```json
{
  "path": "app/profile.tsx",
  "type": "file",
  "content": "import React from 'react'..."
}
```

**Response:**
```json
{
  "success": true,
  "path": "app/profile.tsx"
}
```

---

### 16. Delete File
**DELETE** `/files/{project_id}/{file_path}`

Delete file or folder.

**Response:**
```json
{
  "success": true
}
```

---

### 17. Rename File
**POST** `/files/{project_id}/{file_path}/rename`

Rename file or folder.

**Request:**
```json
{
  "new_name": "home.tsx"
}
```

**Response:**
```json
{
  "success": true,
  "new_name": "home.tsx"
}
```

---

## 🤖 AI-Powered APIs

### 18. Analyze Prompt
**POST** `/analyze-prompt`

Preview what will be created without generating.

**Request:**
```json
{
  "prompt": "Create a task management app"
}
```

**Response:**
```json
{
  "success": true,
  "suggestions": {
    "total_screens": 4,
    "total_images": 3,
    "screens": [
      {
        "name": "Home",
        "description": "Main task list",
        "components": ["TaskCard", "FilterBar"]
      }
    ],
    "images": [
      {
        "name": "hero-image",
        "description": "Main dashboard hero image"
      }
    ]
  },
  "message": "Found 4 screens and 3 images"
}
```

---

### 19. Chat Edit
**POST** `/chat/edit`

AI-powered code editing via natural language.

**Request:**
```json
{
  "project_id": "abc123",
  "prompt": "Add a dark mode toggle to the settings screen"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Updated 2 files",
  "files_modified": ["app/settings.tsx", "theme.ts"],
  "changes_summary": "Added dark mode toggle with theme switching"
}
```

---

### 20. Generate Screen
**POST** `/generate-screen`

Generate new screen/component files.

**Request:**
```json
{
  "project_id": "abc123",
  "prompt": "Create a profile screen with avatar and bio"
}
```

**Response:**
```json
{
  "success": true,
  "files_created": ["app/profile.tsx"],
  "summary": "Created profile screen with avatar and bio fields",
  "message": "Created 1 file(s)"
}
```

---

### 21. Generate Image
**POST** `/generate-image`

Generate AI image for app.

**Request:**
```json
{
  "project_id": "abc123",
  "prompt": "Modern task management dashboard hero image"
}
```

**Response:**
```json
{
  "success": true,
  "filename": "generated_abc123.png",
  "path": "assets/images/generated_abc123.png",
  "image_url": "/projects/abc123/assets/images/generated_abc123.png",
  "message": "Image generated successfully with GEMINI",
  "provider": "gemini",
  "is_placeholder": false
}
```

---

## 🎨 Template APIs

### 22. List Templates
**GET** `/templates` or `/api/templates`

Get all available UI templates.

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "id": "modern-blue",
      "name": "Modern Blue",
      "description": "Clean modern design with blue accents",
      "colors": {
        "primary": "#2563eb",
        "secondary": "#64748b",
        "accent": "#0ea5e9",
        "background": "#ffffff",
        "surface": "#f8fafc",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "border": "#e2e8f0"
      },
      "preview_url": "/template-preview/modern-blue"
    }
  ]
}
```

---

### 23. Get Template Preview
**GET** `/template-preview/{template_id}`

Get HTML preview of template.

**Response:** HTML page with template preview

---

### 24. Apply Template
**POST** `/apply-template`

Apply template to existing project.

**Request:**
```json
{
  "project_id": "abc123",
  "template_id": "modern-blue"
}
```

**Response:**
```json
{
  "success": true,
  "template": "Modern Blue",
  "files_updated": ["app/index.tsx", "app/settings.tsx", "theme.ts"],
  "message": "Applied Modern Blue template to 3 files"
}
```

---

## 📊 Monitoring APIs

### 25. Health Check
**GET** `/health`

System health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-13T10:00:00",
  "active_projects": 2,
  "system_metrics": {
    "cpu_percent": 15.5,
    "memory_percent": 45.2,
    "disk_percent": 12.3
  }
}
```

---

### 26. Metrics
**GET** `/metrics`

Detailed system metrics.

**Response:**
```json
{
  "cpu_percent": 15.5,
  "memory_percent": 45.2,
  "disk_percent": 12.3,
  "active_projects": 2,
  "total_projects_created": 150,
  "average_generation_time": 45.5
}
```

---

### 27. Get Project Logs
**GET** `/logs/{project_id}?hours=24&limit=1000&severity=INFO`

Get Google Cloud logs for project.

**Response:**
```json
{
  "project_id": "abc123",
  "total_logs": 250,
  "time_range_hours": 24,
  "cloud_logging_enabled": true,
  "logs": [
    {
      "timestamp": "2024-11-13T10:00:00",
      "severity": "INFO",
      "message": "Project generation started",
      "resource_type": "cloud_run_revision",
      "labels": {
        "project_id": "abc123"
      }
    }
  ]
}
```

---

## 🔌 WebSocket APIs

### 28. File Watcher
**WebSocket** `/ws/watch/{project_id}`

Real-time file change notifications.

**Connect:**
```javascript
const ws = new WebSocket('wss://backend.run.app/ws/watch/abc123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Files changed:', data.files);
  // data = { type: "file_change", files: ["app/index.tsx"], timestamp: 1234567890 }
};
```

---

### 29. Stream Status
**GET** `/api/v1/stream-status/{project_id}`

Get current streaming generation status.

**Response:**
```json
{
  "project_id": "abc123",
  "status": "generating_code",
  "progress": 45,
  "message": "Generating screen 2 of 4"
}
```

---

## 📋 Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |
| 503 | Service Unavailable (resource limits) |

---

## 🔄 Typical Workflows

### Workflow 1: Generate New App
```
1. POST /generate
   → Returns project_id and preview_url
2. Poll GET /status/{project_id}
   → Check status until "ready"
3. Open preview_url in browser
```

### Workflow 2: Fast Generation with WebSocket
```
1. POST /api/v1/fast-generate
   → Returns project_id and websocket_url
2. Connect to WebSocket
   → Receive real-time updates
3. When status = "ready", use preview_url
```

### Workflow 3: Edit Existing Project
```
1. GET /projects
   → Find project_id
2. POST /chat/edit
   → AI edits files
3. GET /files/{project_id}
   → View updated files
```

### Workflow 4: Reactivate Archived Project
```
1. GET /bucket-projects
   → Find archived project
2. POST /projects/{project_id}/activate
   → Downloads and starts server
3. Use new preview_url
```

---

## 🧪 Testing

```bash
# Test health
curl https://mobile-generator-backend-1098053868371.us-central1.run.app/health

# List projects
curl https://mobile-generator-backend-1098053868371.us-central1.run.app/projects

# Generate app (requires API key)
curl -X POST https://mobile-generator-backend-1098053868371.us-central1.run.app/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"prompt": "Create a todo app"}'
```

---

## 📚 Additional Resources

- **OpenAPI Spec:** Available at `/openapi.json`
- **Interactive Docs:** Available at `/docs`
- **Deployment Guide:** See `DEPLOY.md`
- **Workflow Details:** See `WORKFLOW_IMPROVEMENTS.md`
