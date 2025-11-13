# Shared Dependencies System Guide

## Overview

The system now uses **shared node_modules** to avoid redundant npm installations. This provides:

- ⚡ **Faster project creation** - No npm install needed
- 💾 **Less storage** - node_modules not stored in Cloud Storage
- 🔄 **Consistent dependencies** - All projects use same versions
- 🚀 **Quick loading** - Projects ready instantly

## How It Works

### 1. Project Creation
When you create a new project:
```
✅ Generate code files
✅ Link to shared node_modules (instant)
❌ NO npm install
❌ NO package-lock.json stored
```

### 2. Project Storage (Cloud Storage)
Only essential files are stored:
```
✅ Source code (app/, components/, etc.)
✅ package.json
✅ Configuration files
❌ node_modules (excluded)
❌ package-lock.json (excluded)
❌ .expo cache (excluded)
```

### 3. Project Loading
When you load a project:
```
✅ Download from Cloud Storage
✅ Link to shared node_modules (instant)
✅ Start server immediately
❌ NO npm install
```

## API Endpoints

### Create Project (Automatic Shared Deps)
```bash
POST /generate
{
  "prompt": "Create a todo app",
  "user_id": "user123"
}
```
**Response:**
```json
{
  "project_id": "abc123",
  "preview_url": "https://xyz.ngrok.io",
  "status": "success",
  "message": "App generated with shared dependencies"
}
```

### Build Project with Shared Dependencies
```bash
POST /api/build/projects/{project_id}/build
{
  "use_shared_deps": true,
  "force_rebuild": false
}
```
**Response:**
```json
{
  "project_id": "abc123",
  "status": "success",
  "preview_url": "https://xyz.ngrok.io",
  "message": "Project built successfully",
  "using_shared_deps": true
}
```

### Get Build Status
```bash
GET /api/build/projects/{project_id}/build-status
```
**Response:**
```json
{
  "project_id": "abc123",
  "is_building": true,
  "is_running": true,
  "preview_url": "https://xyz.ngrok.io"
}
```

### Stop Build
```bash
POST /api/build/projects/{project_id}/stop
```

### Rebuild Project
```bash
POST /api/build/projects/{project_id}/rebuild
```

### List Active Builds
```bash
GET /api/build/active-builds
```
**Response:**
```json
{
  "active_builds": ["abc123", "def456"],
  "count": 2
}
```

### Cleanup Old Shared Dependencies
```bash
POST /api/build/cleanup-shared-deps?max_age_days=7
```

## Editor API Endpoints

### Get Project Files
```bash
GET /api/editor/projects/{project_id}/files
```
**Response:**
```json
{
  "project_id": "abc123",
  "file_tree": {
    "name": "project",
    "type": "folder",
    "children": [...]
  }
}
```

### Get File Content
```bash
GET /api/editor/projects/{project_id}/file?path=app/index.tsx
```
**Response:**
```json
{
  "path": "app/index.tsx",
  "content": "import React from 'react'...",
  "language": "typescript"
}
```

### Update File
```bash
POST /api/editor/projects/{project_id}/file
{
  "path": "app/index.tsx",
  "content": "// Updated code..."
}
```

### Delete File
```bash
DELETE /api/editor/projects/{project_id}/file?path=app/old-file.tsx
```

### Start Preview
```bash
POST /api/editor/projects/{project_id}/preview
```

### Stop Preview
```bash
POST /api/editor/projects/{project_id}/stop-preview
```

## Workflow Examples

### Example 1: Create and Preview
```bash
# 1. Create project
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a weather app", "user_id": "user123"}'

# Response: {"project_id": "abc123", "preview_url": "https://xyz.ngrok.io"}

# 2. Project is ready immediately with shared dependencies!
# Open preview_url in Expo Go app
```

### Example 2: Load Existing Project
```bash
# 1. Build project from cloud storage
curl -X POST http://localhost:8000/api/build/projects/abc123/build \
  -H "Content-Type: application/json" \
  -d '{"use_shared_deps": true}'

# Response: {"status": "success", "preview_url": "https://xyz.ngrok.io"}

# 2. Project loads instantly with shared dependencies!
```

### Example 3: Edit and Preview
```bash
# 1. Get file content
curl http://localhost:8000/api/editor/projects/abc123/file?path=app/index.tsx

# 2. Update file
curl -X POST http://localhost:8000/api/editor/projects/abc123/file \
  -H "Content-Type: application/json" \
  -d '{"path": "app/index.tsx", "content": "// New code"}'

# 3. Rebuild to see changes
curl -X POST http://localhost:8000/api/build/projects/abc123/rebuild

# Changes appear in preview immediately!
```

## Benefits

### Storage Savings
```
Traditional approach:
- Project 1: 150MB (code + node_modules)
- Project 2: 150MB (code + node_modules)
- Project 3: 150MB (code + node_modules)
Total: 450MB

Shared dependencies approach:
- Project 1: 2MB (code only)
- Project 2: 2MB (code only)
- Project 3: 2MB (code only)
- Shared: 150MB (one copy)
Total: 156MB (65% savings!)
```

### Speed Improvements
```
Traditional:
- Create project: 5 minutes (npm install)
- Load project: 5 minutes (npm install)

Shared dependencies:
- Create project: 30 seconds (instant link)
- Load project: 10 seconds (instant link)

10x faster! 🚀
```

## Configuration

The shared dependencies are stored in:
```
/tmp/projects/shared_node_modules/
```

Default Expo dependencies included:
- expo ~51.0.0
- react 18.2.0
- react-native 0.74.5
- expo-router ~3.5.0
- @expo/vector-icons ^14.0.0
- And more...

## Troubleshooting

### Issue: Project not showing UI
**Solution:** The project uses Expo Router. Make sure you have proper routing:
```typescript
// app/_layout.tsx
import { Stack } from 'expo-router';

export default function Layout() {
  return <Stack />;
}

// app/index.tsx
import { View, Text } from 'react-native';

export default function Home() {
  return (
    <View>
      <Text>Hello World!</Text>
    </View>
  );
}
```

### Issue: Dependencies not found
**Solution:** Rebuild with shared dependencies:
```bash
curl -X POST http://localhost:8000/api/build/projects/{project_id}/rebuild
```

### Issue: Old cache taking space
**Solution:** Clean up old caches:
```bash
curl -X POST http://localhost:8000/api/build/cleanup-shared-deps?max_age_days=7
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Storage (GCS)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Project 1 │  │Project 2 │  │Project 3 │                  │
│  │(2MB)     │  │(2MB)     │  │(2MB)     │                  │
│  │Code only │  │Code only │  │Code only │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ Download
┌─────────────────────────────────────────────────────────────┐
│                      Local Server                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Project 1 │  │Project 2 │  │Project 3 │                  │
│  │(symlink) │  │(symlink) │  │(symlink) │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       └─────────────┼─────────────┘                         │
│                     ↓                                        │
│            ┌─────────────────┐                              │
│            │ Shared          │                              │
│            │ node_modules    │                              │
│            │ (150MB)         │                              │
│            │ One copy for    │                              │
│            │ all projects    │                              │
│            └─────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Frontend Integration**: Build a web UI that uses these APIs
2. **Real-time Updates**: Use WebSocket for live code changes
3. **Collaborative Editing**: Multiple users editing same project
4. **Version Control**: Track changes and rollback
5. **Custom Dependencies**: Allow projects to add custom packages

## Support

For issues or questions, check the logs:
```bash
# View project logs
curl http://localhost:8000/logs/{project_id}

# View build status
curl http://localhost:8000/api/build/projects/{project_id}/build-status
```
