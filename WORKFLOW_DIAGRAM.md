# Workflow Diagram - Visual Flow

## Complete Workflow Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SUBMITS PROMPT                         │
│  "Create a task management app with priorities and categories"  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: SYSTEM CHECK                         │
│  • Validate inputs (sanitize prompt, user_id)                   │
│  • Check system capacity (CPU, memory, disk)                    │
│  • Verify max concurrent projects limit                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: AI ANALYSIS PHASE ⭐ NEW                   │
│  🤖 AI analyzes prompt and creates complete structure plan      │
│                                                                  │
│  Input: User prompt                                             │
│  Output: {                                                      │
│    "app_name": "taskmaster",                                    │
│    "app_title": "TaskMaster Pro",                               │
│    "description": "Task management app",                        │
│    "screens": [                                                 │
│      {                                                          │
│        "name": "Home",                                          │
│        "file": "index.tsx",                                     │
│        "description": "Main dashboard",                         │
│        "components": ["TaskCard", "FilterBar"],                 │
│        "dummy_data": {"tasks": [...]}                           │
│      },                                                         │
│      ... (all screens)                                          │
│    ],                                                           │
│    "shared_components": ["Button", "Card"],                     │
│    "navigation_type": "tabs"                                    │
│  }                                                              │
│                                                                  │
│  📋 Logs:                                                       │
│  • App Name: taskmaster                                         │
│  • Total Screens: 4                                             │
│  • Shared Components: 4                                         │
│  • Navigation: tabs                                             │
│  • List of all screens with descriptions                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 3: CREATE EXPO PROJECT                           │
│  🚀 Create Expo project with analyzed app name                  │
│                                                                  │
│  • Generate unique name: taskmaster + random suffix             │
│  • Run: npx create-expo-app taskmasterabc123                    │
│  • Create project directory structure                           │
│                                                                  │
│  📋 Logs:                                                       │
│  • App name: taskmasterabc123                                   │
│  • Expo project created at projects/taskmasterabc123            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│      STEP 4: SEQUENTIAL CODE GENERATION ⭐ NEW                  │
│  💻 Generate each screen ONE BY ONE with detailed logging       │
│                                                                  │
│  For each screen in analysis.screens:                           │
│    ┌──────────────────────────────────────────────────┐        │
│    │ 📝 [1/4] Generating: Home Screen                 │        │
│    │    File: app/index.tsx                           │        │
│    │    Description: Main dashboard                   │        │
│    │    Components: TaskCard, FilterBar, AddButton    │        │
│    │    Dummy Data: {"tasks": [...]}                  │        │
│    │    ⏳ Calling AI to generate code...             │        │
│    │    ✓ Screen code written to app/index.tsx       │        │
│    │    ✓ Lines of code: 150                          │        │
│    └──────────────────────────────────────────────────┘        │
│    ┌──────────────────────────────────────────────────┐        │
│    │ 📝 [2/4] Generating: AddTask Screen              │        │
│    │    File: app/add-task.tsx                        │        │
│    │    Description: Create new tasks                 │        │
│    │    Components: TextInput, PrioritySelector       │        │
│    │    Dummy Data: {"priorities": [...]}             │        │
│    │    ⏳ Calling AI to generate code...             │        │
│    │    ✓ Screen code written to app/add-task.tsx    │        │
│    │    ✓ Lines of code: 120                          │        │
│    └──────────────────────────────────────────────────┘        │
│    ... (continues for all screens)                              │
│                                                                  │
│  ✅ CODE GENERATION COMPLETE - 4 screens created                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         STEP 5: APPLY TEMPLATE (Optional)                       │
│  🎨 Apply UI template if specified                              │
│                                                                  │
│  • Read each generated file                                     │
│  • Apply template colors and styles                             │
│  • Write updated files                                          │
│  • Generate theme.ts stylesheet                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 6: PREVIEW SETUP PHASE                        │
│  🔧 Setup preview environment                                   │
│                                                                  │
│  ┌────────────────────────────────────────────┐                │
│  │ 📦 Install Dependencies                    │                │
│  │    • Run: npm install                      │                │
│  │    • Timeout: 10 minutes                   │                │
│  │    ✓ Dependencies installed                │                │
│  └────────────────────────────────────────────┘                │
│                    ▼                                             │
│  ┌────────────────────────────────────────────┐                │
│  │ 🚀 Start Expo Server                       │                │
│  │    • Allocate port (e.g., 8081)            │                │
│  │    • Run: npx expo start --port 8081       │                │
│  │    • Timeout: 90 seconds                   │                │
│  │    ✓ Expo server started (PID: 12345)      │                │
│  └────────────────────────────────────────────┘                │
│                    ▼                                             │
│  ┌────────────────────────────────────────────┐                │
│  │ 🌐 Create Ngrok Tunnel                     │                │
│  │    • Run: ngrok http 8081                  │                │
│  │    • Timeout: 30 seconds                   │                │
│  │    ✓ Tunnel: https://abc123.ngrok.io       │                │
│  └────────────────────────────────────────────┘                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 7: CLOUD STORAGE UPLOAD                          │
│  ☁️  Upload project to Google Cloud Storage                     │
│                                                                  │
│  • Upload all project files to GCS bucket                       │
│  • Path: gs://bucket/projects/taskmaster-abc123                │
│  • Clean up local files after successful upload                 │
│                                                                  │
│  📋 Logs:                                                       │
│  • ✓ Project uploaded to gs://bucket/...                       │
│  • 🧹 Cleaning up local files...                                │
│  • ✓ Local files cleaned up                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 8: MARK AS READY                            │
│  🎉 Project generation complete!                                │
│                                                                  │
│  • Update project status to READY                               │
│  • Record generation metrics                                    │
│  • Return response to user                                      │
│                                                                  │
│  Response: {                                                    │
│    "project_id": "taskmaster-abc123",                           │
│    "preview_url": "https://abc123.ngrok.io",                    │
│    "status": "success",                                         │
│    "message": "App generated with 4 screens",                   │
│    "created_at": "2024-11-13T10:30:00"                          │
│  }                                                              │
│                                                                  │
│  📋 Final Summary Logs:                                         │
│  • ✓ Project ID: taskmaster-abc123                             │
│  • ✓ Preview URL: https://abc123.ngrok.io                      │
│  • ✓ Screens Created: 4                                        │
│  • ✓ Generation Time: 45.23s                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Phase Breakdown

### Phase 1: Analysis (NEW ⭐)
```
Duration: ~5-10 seconds
Purpose: Plan complete app structure before coding
Output: JSON with all screens, components, dummy data
```

### Phase 2: Project Creation
```
Duration: ~30-60 seconds
Purpose: Create Expo project with planned name
Output: Empty Expo project directory
```

### Phase 3: Code Generation (IMPROVED ⭐)
```
Duration: ~20-40 seconds (depends on screen count)
Purpose: Generate each screen sequentially
Output: All screen files with code
Process: Screen 1 → Screen 2 → Screen 3 → ...
```

### Phase 4: Preview Setup
```
Duration: ~60-120 seconds
Purpose: Make app accessible via URL
Output: Live preview URL
Steps: Install deps → Start server → Create tunnel
```

### Phase 5: Cloud Upload
```
Duration: ~10-20 seconds
Purpose: Persist project to cloud
Output: GCS path, local cleanup
```

## Error Handling Flow

```
Any Step Fails
     │
     ▼
┌─────────────────────┐
│ Log Error Details   │
│ • Which phase       │
│ • Which screen      │
│ • Error message     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Status       │
│ status = ERROR      │
│ error_message = ... │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Cleanup Resources   │
│ • Close tunnel      │
│ • Stop server       │
│ • Release port      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Return Error        │
│ Response to User    │
└─────────────────────┘
```

## Parallel vs Sequential

### Old Workflow (Parallel)
```
Create Project
     │
     ├─────────────┬─────────────┐
     ▼             ▼             ▼
Setup Preview  Generate Code  Analyze
     │             │             │
     └─────────────┴─────────────┘
                   │
                   ▼
              Add Screens
```

### New Workflow (Sequential with Analysis)
```
Analyze Prompt (Plan Everything)
     │
     ▼
Create Project
     │
     ▼
Generate Screen 1
     │
     ▼
Generate Screen 2
     │
     ▼
Generate Screen 3
     │
     ▼
Setup Preview
```

## Benefits of New Flow

1. **Predictability**: Know exactly what will be created upfront
2. **Visibility**: See progress for each screen
3. **Debugging**: Easy to identify which screen failed
4. **Control**: Can add pause/resume in future
5. **Quality**: Each screen gets full AI attention
6. **Structure**: Better organized code generation

## Time Comparison

### Old Workflow
```
Total: ~60-90 seconds
├─ Analysis: 0s (none)
├─ Project: 30s
├─ Code Gen: 20s (bulk)
└─ Preview: 40s
```

### New Workflow
```
Total: ~70-100 seconds
├─ Analysis: 10s (NEW)
├─ Project: 30s
├─ Code Gen: 30s (sequential, more screens)
└─ Preview: 40s
```

**Trade-off**: Slightly longer but much better quality and visibility!
