# 5-Step App Creation Flow - Implementation Guide

## Overview
This document describes the complete 5-step app creation process from initial prompt to preview deployment, including how the backend tracks progress and how the frontend should display it.

## The 5 Steps

### Step 1: Create App
**Description:** Initialize project structure and create Expo app  
**Status Tracking:**
- `step_1` - BuildStep with status tracking
- Progress: 0% → 10% (started) → 50% (creating) → 100% (completed)
- Message: "Creating project structure..." → "App structure created: {app_name}"

**Backend Actions:**
1. Create project placeholder
2. AI analyzes prompt to determine app structure
3. Create Expo project with `create-expo-app`
4. Update step status to completed

**API Response:**
- `GET /status/{project_id}` returns `build_steps[0]` with current progress

---

### Step 2: Add Login & Signup Screens
**Description:** Create authentication screens with Firebase backend integration  
**Status Tracking:**
- `step_2` - BuildStep with status tracking
- Progress: 0% → 10% (started) → 100% (completed)
- Message: "Generating authentication screens..." → "Login and Signup screens created"

**Backend Actions:**
1. Generate `app/login.tsx` with Firebase auth integration
2. Generate `app/signup.tsx` with Firebase auth integration
3. Create `lib/supabase.ts` (or Firebase config) if needed
4. Update `app.json` with auth configuration placeholders
5. Update step status to completed

**Files Created:**
- `app/login.tsx`
- `app/signup.tsx`
- `lib/supabase.ts` (or Firebase equivalent)

**API Response:**
- `GET /status/{project_id}` returns `build_steps[1]` with current progress

---

### Step 3: Update index.tsx
**Description:** Set up navigation and routing with Expo Router  
**Status Tracking:**
- `step_3` - BuildStep with status tracking
- Progress: 0% → 100% (completed)
- Message: "Preparing navigation setup..." → "Navigation configured with Expo Router"

**Backend Actions:**
1. Expo Router automatically handles routing based on `app/` directory structure
2. Navigation is configured automatically when screens are created
3. Update step status to completed (after screens are generated)

**Note:** Expo Router uses file-based routing, so navigation is automatically set up when screens are created in the `app/` directory.

**API Response:**
- `GET /status/{project_id}` returns `build_steps[2]` with current progress

---

### Step 4: Add App Screens
**Description:** Generate core app screens based on user prompt  
**Status Tracking:**
- `step_4` - BuildStep with status tracking
- Progress: 0% → 100% (completed)
- Message: "Generating app screens..." → "{N} app screens created"

**Backend Actions:**
1. AI analyzes prompt to determine required screens
2. Generate each screen sequentially:
   - Screen 1: `app/{screen1}.tsx`
   - Screen 2: `app/{screen2}.tsx`
   - Screen 3: `app/{screen3}.tsx`
   - Screen 4: `app/{screen4}.tsx`
3. Each screen includes:
   - React Native components
   - TypeScript types
   - Styling
   - Dummy data for preview
4. Update step status to completed

**Files Created:**
- `app/{screen1}.tsx`
- `app/{screen2}.tsx`
- `app/{screen3}.tsx`
- `app/{screen4}.tsx`
- (Additional screens based on prompt)

**API Response:**
- `GET /status/{project_id}` returns `build_steps[3]` with current progress

---

### Step 5: Run Preview
**Description:** Install dependencies, start server, and create preview tunnel  
**Status Tracking:**
- `step_5` - BuildStep with status tracking
- Progress: 0% → 10% (started) → 30% (deps) → 60% (server) → 80% (tunnel) → 100% (completed)
- Message: "Setting up preview environment..." → "Preview ready at {url}"

**Backend Actions:**
1. **30% Progress:** Install/link dependencies
   - Use shared node_modules for faster setup
   - Link dependencies to project
2. **60% Progress:** Start Expo server
   - Start Metro bundler on allocated port
   - Wait for server to be ready
3. **80% Progress:** Create ngrok tunnel
   - Create public tunnel to local server
   - Get preview URL
4. **100% Progress:** Complete
   - Update project with preview URL
   - Mark step as completed

**API Response:**
- `GET /status/{project_id}` returns:
  - `build_steps[4]` with current progress
  - `preview_url` when completed

---

## API Endpoints

### 1. Create App - `POST /generate`
**Request:**
```json
{
  "prompt": "Create a task management app with home, tasks, profile, and settings screens"
}
```

**Response:**
```json
{
  "project_id": "uuid-here",
  "preview_url": null,
  "status": "initializing",
  "message": "Project created, starting generation...",
  "created_at": "2025-01-18T10:00:00Z"
}
```

**Status:** Returns immediately with project_id. Generation happens asynchronously.

---

### 2. Check Status - `GET /status/{project_id}`
**Response:**
```json
{
  "project_id": "uuid-here",
  "status": "generating_code",
  "preview_url": null,
  "error": null,
  "created_at": "2025-01-18T10:00:00Z",
  "last_active": "2025-01-18T10:02:00Z",
  "current_step": 2,
  "build_steps": [
    {
      "id": "step_1",
      "name": "Create App",
      "description": "Initializing project structure",
      "status": "completed",
      "progress": 100,
      "message": "App structure created: taskmaster1234",
      "started_at": "2025-01-18T10:00:05Z",
      "completed_at": "2025-01-18T10:00:30Z"
    },
    {
      "id": "step_2",
      "name": "Add Login & Signup",
      "description": "Creating authentication screens",
      "status": "in_progress",
      "progress": 50,
      "message": "Generating authentication screens...",
      "started_at": "2025-01-18T10:00:31Z",
      "completed_at": null
    },
    {
      "id": "step_3",
      "name": "Update index.tsx",
      "description": "Setting up navigation and routing",
      "status": "pending",
      "progress": 0,
      "message": null,
      "started_at": null,
      "completed_at": null
    },
    {
      "id": "step_4",
      "name": "Add App Screens",
      "description": "Generating core app screens from prompt",
      "status": "pending",
      "progress": 0,
      "message": null,
      "started_at": null,
      "completed_at": null
    },
    {
      "id": "step_5",
      "name": "Run Preview",
      "description": "Starting server and creating preview",
      "status": "pending",
      "progress": 0,
      "message": null,
      "started_at": null,
      "completed_at": null
    }
  ]
}
```

**Polling:** Frontend should poll this endpoint every 2-3 seconds to get real-time updates.

---

## Frontend Integration Guide

### 1. Chat Interface Flow

#### Initial Request
```typescript
// User sends prompt in chat
const response = await fetch('/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${idToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: userPrompt
  })
});

const { project_id } = await response.json();
```

#### Status Polling
```typescript
// Poll status every 2-3 seconds
const pollStatus = async (projectId: string) => {
  const response = await fetch(`/status/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${idToken}`
    }
  });
  
  const status = await response.json();
  
  // Update UI with current step
  updateChatWithStepProgress(status);
  
  // Continue polling if not complete
  if (status.status !== 'ready' && status.status !== 'error') {
    setTimeout(() => pollStatus(projectId), 2000);
  } else {
    // Show preview URL when ready
    showPreviewUrl(status.preview_url);
  }
};
```

#### Display Progress in Chat
```typescript
function updateChatWithStepProgress(status: ProjectStatusResponse) {
  const currentStep = status.build_steps[status.current_step - 1];
  
  // Add message to chat showing current step
  addChatMessage({
    type: 'system',
    content: `🔄 ${currentStep.name}: ${currentStep.message || currentStep.description}`,
    progress: currentStep.progress,
    step: status.current_step
  });
  
  // Show all steps with checkmarks for completed
  status.build_steps.forEach((step, index) => {
    if (step.status === 'completed') {
      addChatMessage({
        type: 'system',
        content: `✅ Step ${index + 1}: ${step.name} - ${step.message}`,
        step: index + 1
      });
    }
  });
}
```

### 2. Preview Display

When `status.status === 'ready'` and `preview_url` is available:

```typescript
function showPreviewUrl(previewUrl: string) {
  addChatMessage({
    type: 'system',
    content: `🎉 Your app is ready!`,
    preview: {
      url: previewUrl,
      type: 'expo',
      instructions: 'Scan the QR code with Expo Go app or open in web browser'
    }
  });
  
  // Display preview iframe or QR code
  displayPreview(previewUrl);
}
```

### 3. Error Handling

```typescript
if (status.error) {
  addChatMessage({
    type: 'error',
    content: `❌ Error: ${status.error}`,
    suggestion: 'Please try again with a simpler request'
  });
}
```

---

## Step Status Values

- **`pending`**: Step hasn't started yet
- **`in_progress`**: Step is currently running
- **`completed`**: Step finished successfully
- **`failed`**: Step encountered an error

---

## Progress Indicators

Each step has a `progress` field (0-100) that indicates completion percentage:

- **Step 1:** 0% → 10% → 50% → 100%
- **Step 2:** 0% → 10% → 100%
- **Step 3:** 0% → 100% (automatic with Expo Router)
- **Step 4:** 0% → 100% (updates as each screen is generated)
- **Step 5:** 0% → 10% → 30% → 60% → 80% → 100%

---

## Example Chat Flow

```
User: "Create a task management app"

System: "🔄 Step 1: Create App - Creating project structure... (10%)"
System: "✅ Step 1: Create App - App structure created: taskmaster1234"

System: "🔄 Step 2: Add Login & Signup - Generating authentication screens... (10%)"
System: "✅ Step 2: Add Login & Signup - Login and Signup screens created"

System: "🔄 Step 3: Update index.tsx - Preparing navigation setup... (0%)"
System: "✅ Step 3: Update index.tsx - Navigation configured with Expo Router"

System: "🔄 Step 4: Add App Screens - Generating app screens... (0%)"
System: "✅ Step 4: Add App Screens - 4 app screens created"

System: "🔄 Step 5: Run Preview - Setting up preview environment... (10%)"
System: "🔄 Step 5: Run Preview - Installing dependencies... (30%)"
System: "🔄 Step 5: Run Preview - Starting Expo server... (60%)"
System: "🔄 Step 5: Run Preview - Creating preview tunnel... (80%)"
System: "✅ Step 5: Run Preview - Preview ready at https://abc123.ngrok.io"

System: "🎉 Your app is ready! Preview: https://abc123.ngrok.io"
```

---

## Testing

To test the flow:

1. **Start Backend:**
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Create Project:**
   ```bash
   curl -X POST http://localhost:8000/generate \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a simple todo app"}'
   ```

3. **Poll Status:**
   ```bash
   curl http://localhost:8000/status/{project_id} \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Check Preview:**
   - When `status === "ready"`, open `preview_url` in browser
   - Or scan QR code with Expo Go app

---

## Notes

- All steps are tracked in the `Project.build_steps` array
- Steps are updated in real-time as the generation progresses
- Frontend should poll `/status/{project_id}` every 2-3 seconds
- Preview URL is only available after Step 5 completes
- If any step fails, `status.status` will be `"error"` and `error` field will contain details

