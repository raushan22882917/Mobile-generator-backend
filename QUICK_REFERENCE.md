# Quick Reference - Improved Workflow

## What Changed?

### Before (Old Workflow)
```
1. Create Expo project
2. Generate basic code
3. Install deps + Start server + Create tunnel (parallel)
4. Analyze screens (parallel)
5. Generate all screens at once
6. Upload to cloud
```

**Problems:**
- ❌ No visibility into what's being created
- ❌ All screens generated in bulk
- ❌ Hard to debug which screen failed
- ❌ No structure planning upfront

### After (New Workflow)
```
1. AI ANALYSIS PHASE
   - Analyze prompt
   - Decide app name
   - Plan all screens with dummy data
   - Identify components

2. Create Expo project with planned name

3. CODE GENERATION PHASE
   - Generate screen 1 (with logging)
   - Generate screen 2 (with logging)
   - Generate screen 3 (with logging)
   - ... (sequential)

4. PREVIEW SETUP PHASE
   - Install deps
   - Start server
   - Create tunnel

5. Upload to cloud
```

**Benefits:**
- ✅ Complete structure planned upfront
- ✅ Screens generated one by one
- ✅ Detailed logging for each screen
- ✅ Easy to debug failures
- ✅ Better progress visibility

## Log Output Comparison

### Old Logs
```
INFO: Generating code for project abc123
INFO: Code generated successfully
INFO: Installing dependencies
INFO: Starting server
```

### New Logs
```
================================================================================
🤖 AI ANALYSIS PHASE - Analyzing prompt and planning app structure
================================================================================
📊 Analyzing app requirements...

📋 APP STRUCTURE ANALYSIS COMPLETE
📱 App Name: taskmaster
📄 Total Screens: 4

📄 SCREENS TO BE CREATED:
  1. Home (index.tsx) - Main dashboard
  2. AddTask (add-task.tsx) - Create new tasks
  3. TaskDetail (task-detail.tsx) - View task details
  4. Settings (settings.tsx) - App settings

================================================================================
💻 CODE GENERATION PHASE - Creating screens sequentially
================================================================================

📝 [1/4] Generating: Home Screen
   File: app/index.tsx
   Description: Main dashboard showing all tasks
   ⏳ Calling AI to generate code...
   ✓ Screen code written to app/index.tsx
   ✓ Lines of code: 150

📝 [2/4] Generating: AddTask Screen
   File: app/add-task.tsx
   Description: Create new tasks form
   ⏳ Calling AI to generate code...
   ✓ Screen code written to app/add-task.tsx
   ✓ Lines of code: 120

... (continues for all screens)

✅ CODE GENERATION COMPLETE - 4 screens created

================================================================================
🔧 PREVIEW SETUP PHASE
================================================================================
📦 Installing dependencies...
✓ Dependencies installed
🚀 Starting Expo server on port 8081...
✓ Expo server started
🌐 Creating ngrok tunnel...
✓ Tunnel created: https://abc123.ngrok.io

================================================================================
🎉 PROJECT GENERATION COMPLETE!
================================================================================
✓ Project ID: taskmaster-abc123
✓ Preview URL: https://abc123.ngrok.io
✓ Screens Created: 4
✓ Generation Time: 45.23s
```

## AI Analysis Output

The AI now returns a structured JSON with complete app plan:

```json
{
  "app_name": "taskmaster",
  "app_title": "TaskMaster Pro",
  "description": "Task management app with priorities",
  "screens": [
    {
      "name": "Home",
      "file": "index.tsx",
      "description": "Main dashboard showing all tasks",
      "components": ["TaskCard", "FilterBar", "AddButton"],
      "dummy_data": {
        "tasks": [
          {
            "id": 1,
            "title": "Complete project",
            "priority": "high",
            "completed": false
          }
        ]
      }
    }
  ],
  "shared_components": ["Button", "Card", "Header"],
  "navigation_type": "tabs"
}
```

## Code Generation Process

Each screen is generated individually with this prompt:

```
Generate a complete React Native Expo screen file.

Screen Details:
- Name: Home
- File: index.tsx
- Description: Main dashboard showing all tasks
- Components needed: TaskCard, FilterBar, AddButton
- Dummy data: {"tasks": [...]}

App Context:
- App: TaskMaster Pro
- Navigation: tabs

Requirements:
1. Use TypeScript with proper types
2. Include the dummy data in the component
3. Use React Native components
4. Make it responsive and styled
5. Add proper imports
6. Use functional components with hooks
7. Include inline styles using StyleSheet
```

## Testing the New Workflow

### 1. Run the demonstration:
```bash
python test_improved_workflow.py
```

### 2. Test with real API:
```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "Create a task management app with priorities",
    "user_id": "test-user"
  }'
```

### 3. Watch the logs:
The backend will show detailed progress for each phase.

## Key Files Modified

- `main.py` - Updated `/generate` endpoint with new workflow
- `test_improved_workflow.py` - Demonstration script
- `WORKFLOW_IMPROVEMENTS.md` - Detailed documentation

## Emoji Legend

- 🤖 AI Analysis
- 📊 Processing
- 📋 Results
- 📱 App Info
- 📝 Description
- 🧭 Navigation
- 📄 Screens
- 🧩 Components
- 🚀 Starting
- ✓ Success
- ⏳ In Progress
- 💻 Code Generation
- 🔧 Setup
- 📦 Dependencies
- 🌐 Network
- ☁️ Cloud
- 🧹 Cleanup
- 🎉 Complete
- ⚠️ Warning
- ❌ Error

## Next Steps

1. ✅ AI analysis phase implemented
2. ✅ Sequential screen generation implemented
3. ✅ Detailed logging implemented
4. 🔄 Test with real prompts
5. 🔄 Add WebSocket streaming for frontend
6. 🔄 Add retry logic for failed screens
7. 🔄 Add screen preview before finalizing
