# Frontend App Creation Plan - Complete Integration Guide

This document provides a complete plan for integrating the 5-step app creation flow in your frontend.

## Overview

**All APIs are already built!** ✅ You just need to integrate them in the correct sequence.

## The 5-Step Process

1. **Create App** - Initialize project structure
2. **Add Login & Signup Screens** - Authentication screens
3. **Update index.tsx** - Main entry point with navigation
4. **Add 4 Prompt-Related Screens** - Core app screens based on prompt
5. **Run Preview** - Start server and show preview URL

---

## API Endpoints Summary

| Step | API Endpoint | Method | Purpose | Status |
|------|--------------|--------|---------|--------|
| Auth | `/auth/login` | POST | User authentication | ✅ Built |
| 1-4 | `/generate` | POST | Creates app + all screens automatically | ✅ Built |
| Track | `/status/{project_id}` | GET | Check project status | ✅ Built |
| 4 (Optional) | `/generate-screen` | POST | Add individual screens | ✅ Built |
| 3 (Optional) | `/chat/edit` | POST | Edit files (like index.tsx) | ✅ Built |
| 5 | `/projects/{project_id}/activate` | POST | Activate/reactivate project | ✅ Built |
| Files | `/files/{project_id}` | GET | Get project file tree | ✅ Built |

---

## Two Approaches

### Approach 1: Automatic (Recommended) - Single API Call

The `/generate` endpoint **automatically does steps 1-4** in one call!

**Flow:**
```
1. User enters prompt
2. Call POST /generate
3. Backend automatically:
   - Creates app structure
   - Adds login.tsx and signup.tsx
   - Creates screens based on prompt analysis
   - Updates navigation
4. Poll GET /status/{project_id} until ready
5. Show preview_url
```

### Approach 2: Manual Step-by-Step (For Custom Control)

If you want more control over each step:

```
1. Create app structure (use /generate with minimal prompt)
2. Add login/signup (use /generate-screen)
3. Update index.tsx (use /chat/edit)
4. Add 4 screens (use /generate-screen 4 times)
5. Activate (use /projects/{id}/activate)
```

---

## Complete Frontend Integration Code

### Step 0: Authentication Setup

```javascript
// auth.js
const API_BASE_URL = 'https://your-backend-url.com';

// Login user
export const login = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (data.success) {
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }
  
  throw new Error(data.message);
};

// Get auth token for requests
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Make authenticated request
export const authenticatedFetch = async (url, options = {}) => {
  const token = getAuthToken();
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
};
```

### Step 1-4: Create App (Automatic Approach)

```javascript
// appCreation.js

/**
 * Create new app - This does steps 1-4 automatically!
 */
export const createApp = async (prompt, templateId = null) => {
  const response = await authenticatedFetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    body: JSON.stringify({
      prompt: prompt,
      template_id: templateId, // Optional: UI template
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to create app');
  }
  
  const data = await response.json();
  
  // Returns: { project_id, preview_url, status, message, created_at }
  return data;
};

/**
 * Poll project status until ready
 */
export const pollProjectStatus = async (projectId, onStatusUpdate = null) => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const response = await authenticatedFetch(
          `${API_BASE_URL}/status/${projectId}`
        );
        
        if (!response.ok) {
          reject(new Error('Failed to get project status'));
          return;
        }
        
        const status = await response.json();
        
        // Callback for UI updates
        if (onStatusUpdate) {
          onStatusUpdate(status);
        }
        
        // Check if ready
        if (status.status === 'ready') {
          resolve(status);
        } else if (status.status === 'error') {
          reject(new Error(status.error || 'Project generation failed'));
        } else {
          // Continue polling
          setTimeout(poll, 2000); // Poll every 2 seconds
        }
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
};

/**
 * Map backend status to step number for UI
 */
export const getStepFromStatus = (status) => {
  const statusMap = {
    'initializing': 1,
    'generating_code': 2,
    'installing_deps': 3,
    'starting_server': 4,
    'creating_tunnel': 5,
    'ready': 6, // Complete
    'error': -1,
  };
  
  return statusMap[status] || 0;
};

/**
 * Get step label for UI
 */
export const getStepLabel = (step) => {
  const labels = {
    1: 'Creating app structure...',
    2: 'Generating code and screens...',
    3: 'Installing dependencies...',
    4: 'Starting server...',
    5: 'Creating preview tunnel...',
    6: 'Ready! Preview available',
    -1: 'Error occurred',
  };
  
  return labels[step] || 'Processing...';
};
```

### Step 5: Preview & Activation

```javascript
/**
 * Activate/reactivate a project
 */
export const activateProject = async (projectId) => {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/projects/${projectId}/activate`,
    { method: 'POST' }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to activate project');
  }
  
  return await response.json();
};

/**
 * Get project files tree
 */
export const getProjectFiles = async (projectId) => {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/files/${projectId}`
  );
  
  if (!response.ok) {
    throw new Error('Failed to get project files');
  }
  
  return await response.json();
};
```

### Optional: Manual Screen Generation

```javascript
/**
 * Generate individual screen (for step 4 if not using automatic)
 */
export const generateScreen = async (projectId, prompt) => {
  const response = await authenticatedFetch(`${API_BASE_URL}/generate-screen`, {
    method: 'POST',
    body: JSON.stringify({
      project_id: projectId,
      prompt: prompt,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to generate screen');
  }
  
  return await response.json();
};

/**
 * Edit file using AI (for step 3 if needed)
 */
export const editFile = async (projectId, prompt) => {
  const response = await authenticatedFetch(`${API_BASE_URL}/chat/edit`, {
    method: 'POST',
    body: JSON.stringify({
      project_id: projectId,
      prompt: prompt,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to edit file');
  }
  
  return await response.json();
};
```

---

## Complete React Component Example

```jsx
// AppCreationFlow.jsx
import React, { useState } from 'react';
import { createApp, pollProjectStatus, getStepFromStatus, getStepLabel } from './appCreation';
import { login } from './auth';

const AppCreationFlow = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [projectId, setProjectId] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const steps = [
    { id: 1, label: 'Create App', description: 'Initializing project structure' },
    { id: 2, label: 'Add Login & Signup', description: 'Creating authentication screens' },
    { id: 3, label: 'Update index.tsx', description: 'Setting up navigation' },
    { id: 4, label: 'Add App Screens', description: 'Generating 4 core screens' },
    { id: 5, label: 'Run Preview', description: 'Starting server and creating preview' },
  ];

  const handleCreateApp = async () => {
    if (!prompt.trim()) {
      setError('Please enter an app description');
      return;
    }

    setIsLoading(true);
    setError(null);
    setCurrentStep(1);

    try {
      // Step 1-4: Create app (automatic)
      const result = await createApp(prompt);
      setProjectId(result.project_id);
      setCurrentStep(2);

      // Poll status to track progress
      await pollProjectStatus(result.project_id, (status) => {
        const step = getStepFromStatus(status.status);
        if (step > 0) {
          setCurrentStep(Math.min(step, 5));
        }
        
        // Update preview URL when available
        if (status.preview_url) {
          setPreviewUrl(status.preview_url);
        }
        
        // Handle errors
        if (status.status === 'error') {
          setError(status.error || 'Generation failed');
          setIsLoading(false);
        }
      });

      // Step 5: Ready!
      setCurrentStep(6);
      setIsLoading(false);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  return (
    <div className="app-creation-flow">
      <h1>Create New App</h1>
      
      <div className="prompt-input">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your app... (e.g., 'A todo app with categories, filters, and reminders')"
          rows={5}
        />
        <button 
          onClick={handleCreateApp} 
          disabled={isLoading || !prompt.trim()}
        >
          {isLoading ? 'Creating...' : 'Create App'}
        </button>
      </div>

      {/* Progress Steps */}
      <div className="steps-container">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`step ${currentStep >= step.id ? 'active' : ''} ${
              currentStep > step.id ? 'completed' : ''
            }`}
          >
            <div className="step-number">{step.id}</div>
            <div className="step-content">
              <h3>{step.label}</h3>
              <p>{step.description}</p>
            </div>
            {currentStep > step.id && <span className="check">✓</span>}
          </div>
        ))}
      </div>

      {/* Status Messages */}
      {isLoading && (
        <div className="status-message">
          <p>{getStepLabel(currentStep)}</p>
        </div>
      )}

      {/* Preview URL */}
      {previewUrl && (
        <div className="preview-section">
          <h2>🎉 Your app is ready!</h2>
          <p>Preview URL: <a href={previewUrl} target="_blank">{previewUrl}</a></p>
          <div className="preview-instructions">
            <h3>How to preview:</h3>
            <ol>
              <li>Install Expo Go app on your phone</li>
              <li>Open the preview URL above</li>
              <li>Scan the QR code with Expo Go</li>
              <li>Your app will load on your device!</li>
            </ol>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <p>❌ Error: {error}</p>
        </div>
      )}
    </div>
  );
};

export default AppCreationFlow;
```

---

## Status Mapping for UI

The backend returns these statuses. Map them to your UI steps:

```javascript
const STATUS_TO_STEP = {
  'initializing': {
    step: 1,
    label: 'Creating app structure...',
    progress: 20
  },
  'generating_code': {
    step: 2,
    label: 'Generating code and screens (Login, Signup, App screens)...',
    progress: 40
  },
  'installing_deps': {
    step: 3,
    label: 'Installing dependencies...',
    progress: 60
  },
  'starting_server': {
    step: 4,
    label: 'Starting Expo server...',
    progress: 80
  },
  'creating_tunnel': {
    step: 5,
    label: 'Creating preview tunnel...',
    progress: 90
  },
  'ready': {
    step: 6,
    label: '✅ Ready! Preview available',
    progress: 100
  },
  'error': {
    step: -1,
    label: '❌ Error occurred',
    progress: 0
  }
};
```

---

## Complete Flow Diagram

```
User Input (Prompt)
    ↓
[POST /auth/login] → Get Token
    ↓
[POST /generate] → Create App (Steps 1-4 automatic)
    ↓
    ├─→ Creates project structure
    ├─→ Adds login.tsx & signup.tsx
    ├─→ Analyzes prompt → Creates screens
    └─→ Updates navigation
    ↓
[GET /status/{id}] → Poll every 2 seconds
    ↓
    ├─→ Status: initializing → Step 1
    ├─→ Status: generating_code → Step 2-4
    ├─→ Status: installing_deps → Step 3
    ├─→ Status: starting_server → Step 4
    ├─→ Status: creating_tunnel → Step 5
    └─→ Status: ready → Show preview_url
    ↓
Display Preview URL
    ↓
User scans QR code → App opens in Expo Go
```

---

## What `/generate` Automatically Does

When you call `POST /generate`, the backend:

1. ✅ **Creates Expo project** with proper structure
2. ✅ **Analyzes your prompt** to determine screens needed
3. ✅ **Generates login.tsx** - Complete login screen
4. ✅ **Generates signup.tsx** - Complete signup screen
5. ✅ **Generates app screens** - Based on prompt analysis (usually 3-5 screens)
6. ✅ **Sets up navigation** - Configures routing
7. ✅ **Installs dependencies** - Links shared node_modules
8. ✅ **Starts Expo server** - On allocated port
9. ✅ **Creates tunnel** - Ngrok tunnel for preview
10. ✅ **Returns preview_url** - Ready to use!

**So you only need ONE API call for steps 1-4!**

---

## Optional: Manual Control

If you want to control each step separately:

```javascript
// Step 1: Create minimal app
const project = await createApp("Basic app structure");

// Step 2: Add login screen
await generateScreen(project.project_id, "Create a login screen with email and password fields");

// Step 3: Add signup screen  
await generateScreen(project.project_id, "Create a signup screen with email, password, and confirm password");

// Step 4: Update index.tsx
await editFile(project.project_id, "Update index.tsx to show login screen first, then navigate to main app after authentication");

// Step 5: Add 4 app screens
const screens = [
  "Create a home screen with welcome message",
  "Create a profile screen with user info",
  "Create a settings screen",
  "Create a dashboard screen"
];

for (const screenPrompt of screens) {
  await generateScreen(project.project_id, screenPrompt);
}

// Step 6: Activate
await activateProject(project.project_id);
```

---

## Error Handling

```javascript
try {
  const result = await createApp(prompt);
  // Success
} catch (error) {
  if (error.message.includes('401')) {
    // Authentication error - redirect to login
  } else if (error.message.includes('429')) {
    // Rate limit - show retry message
  } else {
    // Other error - show error message
  }
}
```

---

## Summary

✅ **All APIs are built and ready!**

**Simplest Integration:**
1. Call `POST /generate` with user's prompt
2. Poll `GET /status/{project_id}` every 2 seconds
3. Show progress based on status
4. Display `preview_url` when status is "ready"

**That's it!** The backend handles everything automatically.

For more control, use the individual endpoints (`/generate-screen`, `/chat/edit`, etc.) but the automatic approach is recommended for most use cases.

