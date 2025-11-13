# Frontend Integration Guide

## Backend URL
```javascript
const BACKEND_URL = 'https://mobile-generator-backend-1098053868371.us-central1.run.app';
const API_KEY = 'your-api-key-here'; // Optional, if REQUIRE_API_KEY=true
```

---

## 🚀 Quick Start - API Service Class

Create a reusable API service:

```javascript
// services/api.js
class AppBuilderAPI {
  constructor(baseURL, apiKey = null) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'API request failed');
    }

    return response.json();
  }

  // Generate app
  async generateApp(prompt, userId = 'anonymous', templateId = null) {
    return this.request('/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, user_id: userId, template_id: templateId }),
    });
  }

  // Fast generate with WebSocket
  async fastGenerate(prompt, userId = 'anonymous', templateId = null) {
    return this.request('/api/v1/fast-generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, user_id: userId, template_id: templateId }),
    });
  }

  // Get project status
  async getStatus(projectId) {
    return this.request(`/status/${projectId}`);
  }

  // List all projects
  async listProjects() {
    return this.request('/projects');
  }

  // Get project files
  async getProjectFiles(projectId) {
    return this.request(`/files/${projectId}`);
  }

  // Update file
  async updateFile(projectId, filePath, content) {
    return this.request(`/files/${projectId}/${filePath}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  // Chat edit
  async chatEdit(projectId, prompt) {
    return this.request('/chat/edit', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, prompt }),
    });
  }

  // List templates
  async listTemplates() {
    return this.request('/templates');
  }

  // Apply template
  async applyTemplate(projectId, templateId) {
    return this.request('/apply-template', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, template_id: templateId }),
    });
  }

  // Activate project
  async activateProject(projectId) {
    return this.request(`/projects/${projectId}/activate`, {
      method: 'POST',
    });
  }

  // Analyze prompt
  async analyzePrompt(prompt) {
    return this.request('/analyze-prompt', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

// Export singleton instance
export const api = new AppBuilderAPI(
  'https://mobile-generator-backend-1098053868371.us-central1.run.app',
  null // Add API key if needed
);
```

---

## 📱 React Examples

### 1. Generate App Component

```jsx
// components/AppGenerator.jsx
import React, { useState } from 'react';
import { api } from '../services/api';

export default function AppGenerator() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.generateApp(prompt);
      setResult(response);
      
      // Start polling for status
      pollStatus(response.project_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const pollStatus = async (projectId) => {
    const interval = setInterval(async () => {
      try {
        const status = await api.getStatus(projectId);
        
        if (status.status === 'ready') {
          clearInterval(interval);
          setResult(prev => ({ ...prev, ...status }));
        } else if (status.status === 'error') {
          clearInterval(interval);
          setError(status.error);
        }
      } catch (err) {
        clearInterval(interval);
        setError(err.message);
      }
    }, 3000); // Poll every 3 seconds
  };

  return (
    <div className="app-generator">
      <h2>Generate Your App</h2>
      
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your app... (e.g., Create a task management app with priorities)"
        rows={5}
        style={{ width: '100%', padding: '10px' }}
      />
      
      <button 
        onClick={handleGenerate} 
        disabled={loading || !prompt}
        style={{ marginTop: '10px', padding: '10px 20px' }}
      >
        {loading ? 'Generating...' : 'Generate App'}
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          Error: {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ccc' }}>
          <h3>✅ App Generated!</h3>
          <p><strong>Project ID:</strong> {result.project_id}</p>
          <p><strong>Status:</strong> {result.status}</p>
          {result.preview_url && (
            <p>
              <strong>Preview:</strong>{' '}
              <a href={result.preview_url} target="_blank" rel="noopener noreferrer">
                Open App
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### 2. Fast Generate with WebSocket

```jsx
// components/FastGenerator.jsx
import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

export default function FastGenerator() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [progress, setProgress] = useState([]);
  const [previewUrl, setPreviewUrl] = useState(null);
  const wsRef = useRef(null);

  const handleGenerate = async () => {
    setLoading(true);
    setProgress([]);
    setStatus('Initializing...');
    
    try {
      const response = await api.fastGenerate(prompt);
      
      // Connect to WebSocket
      connectWebSocket(response.websocket_url, response.project_id);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
      setLoading(false);
    }
  };

  const connectWebSocket = (wsUrl, projectId) => {
    // Convert https to wss
    const url = wsUrl.replace('https://', 'wss://').replace('http://', 'ws://');
    
    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setProgress(prev => [...prev, '🔌 Connected to server']);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setStatus(data.status || data.message);
      setProgress(prev => [...prev, `${data.status}: ${data.message}`]);
      
      if (data.preview_url) {
        setPreviewUrl(data.preview_url);
      }
      
      if (data.status === 'ready' || data.status === 'error') {
        setLoading(false);
        wsRef.current?.close();
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('WebSocket connection error');
      setLoading(false);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket closed');
    };
  };

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return (
    <div className="fast-generator">
      <h2>Fast Generate (Real-time Updates)</h2>
      
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your app..."
        rows={5}
        style={{ width: '100%', padding: '10px' }}
      />
      
      <button 
        onClick={handleGenerate} 
        disabled={loading || !prompt}
        style={{ marginTop: '10px', padding: '10px 20px' }}
      >
        {loading ? 'Generating...' : 'Generate App'}
      </button>

      {status && (
        <div style={{ marginTop: '20px' }}>
          <h3>Status: {status}</h3>
        </div>
      )}

      {progress.length > 0 && (
        <div style={{ marginTop: '20px', maxHeight: '300px', overflow: 'auto' }}>
          <h4>Progress Log:</h4>
          {progress.map((msg, idx) => (
            <div key={idx} style={{ padding: '5px', borderBottom: '1px solid #eee' }}>
              {msg}
            </div>
          ))}
        </div>
      )}

      {previewUrl && (
        <div style={{ marginTop: '20px', padding: '15px', background: '#e8f5e9' }}>
          <h3>✅ App Ready!</h3>
          <a href={previewUrl} target="_blank" rel="noopener noreferrer">
            Open Preview
          </a>
        </div>
      )}
    </div>
  );
}
```

---

### 3. Project List Component

```jsx
// components/ProjectList.jsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, local: 0, cloud: 0 });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.listProjects();
      setProjects(data.projects);
      setStats({
        total: data.total,
        local: data.local_count,
        cloud: data.cloud_count,
      });
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (projectId) => {
    try {
      const result = await api.activateProject(projectId);
      alert(`Project activated! URL: ${result.preview_url}`);
      loadProjects(); // Refresh list
    } catch (err) {
      alert(`Failed to activate: ${err.message}`);
    }
  };

  if (loading) return <div>Loading projects...</div>;

  return (
    <div className="project-list">
      <h2>Your Projects</h2>
      
      <div style={{ marginBottom: '20px', padding: '10px', background: '#f5f5f5' }}>
        <strong>Total:</strong> {stats.total} | 
        <strong> Local:</strong> {stats.local} | 
        <strong> Cloud:</strong> {stats.cloud}
      </div>

      {projects.length === 0 ? (
        <p>No projects yet. Generate your first app!</p>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {projects.map((project) => (
            <div 
              key={project.id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: '15px', 
                borderRadius: '8px' 
              }}
            >
              <h3>{project.name}</h3>
              <p><strong>Status:</strong> {project.status}</p>
              <p><strong>Source:</strong> {project.source}</p>
              <p><strong>Created:</strong> {new Date(project.created_at).toLocaleString()}</p>
              
              {project.preview_url ? (
                <a 
                  href={project.preview_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ marginRight: '10px' }}
                >
                  Open Preview
                </a>
              ) : (
                <button onClick={() => handleActivate(project.id)}>
                  Activate Project
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### 4. Chat Edit Component

```jsx
// components/ChatEdit.jsx
import React, { useState } from 'react';
import { api } from '../services/api';

export default function ChatEdit({ projectId }) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleEdit = async () => {
    setLoading(true);
    setResult(null);
    
    try {
      const response = await api.chatEdit(projectId, prompt);
      setResult(response);
      setPrompt('');
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-edit">
      <h3>AI Chat Edit</h3>
      
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe changes... (e.g., Add a dark mode toggle)"
        rows={3}
        style={{ width: '100%', padding: '10px' }}
      />
      
      <button 
        onClick={handleEdit} 
        disabled={loading || !prompt}
        style={{ marginTop: '10px' }}
      >
        {loading ? 'Processing...' : 'Apply Changes'}
      </button>

      {result && (
        <div style={{ marginTop: '15px', padding: '10px', background: '#e8f5e9' }}>
          <p><strong>✅ {result.message}</strong></p>
          <p><strong>Files Modified:</strong></p>
          <ul>
            {result.files_modified.map((file, idx) => (
              <li key={idx}>{file}</li>
            ))}
          </ul>
          <p><em>{result.changes_summary}</em></p>
        </div>
      )}
    </div>
  );
}
```

---

### 5. Template Selector Component

```jsx
// components/TemplateSelector.jsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function TemplateSelector({ onSelect, selectedId }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await api.listTemplates();
      setTemplates(data.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading templates...</div>;

  return (
    <div className="template-selector">
      <h3>Choose a Template</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '15px' }}>
        {templates.map((template) => (
          <div
            key={template.id}
            onClick={() => onSelect(template.id)}
            style={{
              border: selectedId === template.id ? '3px solid blue' : '1px solid #ddd',
              padding: '15px',
              borderRadius: '8px',
              cursor: 'pointer',
              background: selectedId === template.id ? '#e3f2fd' : 'white',
            }}
          >
            <h4>{template.name}</h4>
            <p style={{ fontSize: '12px', color: '#666' }}>{template.description}</p>
            
            <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
              <div 
                style={{ 
                  width: '30px', 
                  height: '30px', 
                  background: template.colors.primary,
                  borderRadius: '4px' 
                }} 
              />
              <div 
                style={{ 
                  width: '30px', 
                  height: '30px', 
                  background: template.colors.secondary,
                  borderRadius: '4px' 
                }} 
              />
              <div 
                style={{ 
                  width: '30px', 
                  height: '30px', 
                  background: template.colors.accent,
                  borderRadius: '4px' 
                }} 
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🎯 Vue.js Examples

### Vue Composition API

```vue
<!-- components/AppGenerator.vue -->
<template>
  <div class="app-generator">
    <h2>Generate Your App</h2>
    
    <textarea
      v-model="prompt"
      placeholder="Describe your app..."
      rows="5"
    />
    
    <button @click="handleGenerate" :disabled="loading || !prompt">
      {{ loading ? 'Generating...' : 'Generate App' }}
    </button>

    <div v-if="error" class="error">
      Error: {{ error }}
    </div>

    <div v-if="result" class="result">
      <h3>✅ App Generated!</h3>
      <p><strong>Project ID:</strong> {{ result.project_id }}</p>
      <p><strong>Status:</strong> {{ result.status }}</p>
      <a v-if="result.preview_url" :href="result.preview_url" target="_blank">
        Open Preview
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '../services/api';

const prompt = ref('');
const loading = ref(false);
const result = ref(null);
const error = ref(null);

const handleGenerate = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const response = await api.generateApp(prompt.value);
    result.value = response;
    pollStatus(response.project_id);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const pollStatus = async (projectId) => {
  const interval = setInterval(async () => {
    try {
      const status = await api.getStatus(projectId);
      
      if (status.status === 'ready') {
        clearInterval(interval);
        result.value = { ...result.value, ...status };
      } else if (status.status === 'error') {
        clearInterval(interval);
        error.value = status.error;
      }
    } catch (err) {
      clearInterval(interval);
      error.value = err.message;
    }
  }, 3000);
};
</script>

<style scoped>
.app-generator {
  padding: 20px;
}

textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
}

button {
  padding: 10px 20px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: red;
  margin-top: 10px;
}

.result {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
```

---

## 🔥 Next.js App Router Example

```typescript
// app/generate/page.tsx
'use client';

import { useState } from 'react';
import { api } from '@/services/api';

export default function GeneratePage() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    setLoading(true);
    
    try {
      const response = await api.generateApp(prompt);
      setResult(response);
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Generate Your App</h1>
      
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your app..."
        rows={5}
        className="w-full p-4 border rounded-lg"
      />
      
      <button
        onClick={handleGenerate}
        disabled={loading || !prompt}
        className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg disabled:bg-gray-400"
      >
        {loading ? 'Generating...' : 'Generate App'}
      </button>

      {result && (
        <div className="mt-6 p-6 bg-green-50 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">✅ App Generated!</h2>
          <p><strong>Project ID:</strong> {result.project_id}</p>
          {result.preview_url && (
            <a 
              href={result.preview_url} 
              target="_blank"
              className="text-blue-600 underline"
            >
              Open Preview
            </a>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 📦 Environment Variables

Create `.env.local` in your frontend:

```env
NEXT_PUBLIC_BACKEND_URL=https://mobile-generator-backend-1098053868371.us-central1.run.app
NEXT_PUBLIC_API_KEY=your-api-key-here
```

---

## 🧪 Testing the Connection

```javascript
// test-connection.js
import { api } from './services/api';

async function testConnection() {
  try {
    // Test health
    const health = await api.healthCheck();
    console.log('✅ Health:', health);

    // Test list projects
    const projects = await api.listProjects();
    console.log('✅ Projects:', projects);

    // Test list templates
    const templates = await api.listTemplates();
    console.log('✅ Templates:', templates);

    console.log('🎉 All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testConnection();
```

---

## 🚀 Ready to Use!

Your frontend is now connected to the backend. Use the components above or adapt them to your framework!
