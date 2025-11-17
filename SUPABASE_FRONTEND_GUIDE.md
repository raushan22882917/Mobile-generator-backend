# Supabase Integration Guide for Frontend

## Overview
This guide explains what new API endpoints and frontend features need to be added to support Supabase authentication in generated projects.

---

## 🔌 New API Endpoints to Add

### 1. Update Supabase Configuration
**Endpoint:** `PUT /projects/{project_id}/supabase-config`

**Purpose:** Allow users to update Supabase credentials after project generation.

**Request Body:**
```json
{
  "supabase_url": "https://xxxxx.supabase.co",
  "supabase_anon_key": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Supabase configuration updated",
  "project_id": "abc123"
}
```

**Implementation:**
- Updates `.env` file in project directory
- Updates `app.json` extra section
- Validates URL format
- Returns success/error

---

### 2. Get Supabase Configuration Status
**Endpoint:** `GET /projects/{project_id}/supabase-config`

**Purpose:** Check if Supabase is configured for a project.

**Response:**
```json
{
  "configured": true,
  "has_url": true,
  "has_key": true,
  "message": "Supabase is configured"
}
```

---

### 3. Test Supabase Connection
**Endpoint:** `POST /projects/{project_id}/test-supabase`

**Purpose:** Test if Supabase credentials are valid.

**Request Body:**
```json
{
  "supabase_url": "https://xxxxx.supabase.co",
  "supabase_anon_key": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "project_name": "My Supabase Project"
}
```

---

## 🎨 Frontend Features to Add

### 1. Supabase Configuration Modal/Form

**Location:** Project settings or project details page

**Features:**
- Input fields for Supabase URL and Anon Key
- "Get Credentials" button linking to Supabase dashboard
- Test connection button
- Save configuration
- Visual indicator if configured/not configured

**Component Structure:**
```typescript
// SupabaseConfigModal.tsx
interface SupabaseConfigModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

// Features:
// - Form with URL and Key inputs
// - Validation
// - Test connection
// - Save to backend
// - Show success/error messages
```

---

### 2. Supabase Setup Wizard

**Location:** After project generation, show setup wizard

**Steps:**
1. **Welcome Screen**
   - Explain what Supabase is
   - Benefits of authentication
   - "Get Started" button

2. **Credentials Input**
   - Guide user to Supabase dashboard
   - Input form for URL and Key
   - "Where to find these?" help link

3. **Test Connection**
   - Test button
   - Show success/error
   - "Continue" button

4. **Complete**
   - Success message
   - "View Project" button
   - "Skip for now" option

**Component Structure:**
```typescript
// SupabaseSetupWizard.tsx
interface SupabaseSetupWizardProps {
  projectId: string;
  onComplete: () => void;
  onSkip: () => void;
}

// Multi-step wizard with:
// - Step 1: Introduction
// - Step 2: Credentials input
// - Step 3: Test connection
// - Step 4: Success
```

---

### 3. Project Status Badge

**Location:** Project card/list item

**Features:**
- Show "Supabase Configured" badge
- Show "Supabase Not Configured" warning
- Click to open configuration modal

**Component:**
```typescript
// SupabaseStatusBadge.tsx
interface SupabaseStatusBadgeProps {
  projectId: string;
  isConfigured: boolean;
  onClick?: () => void;
}
```

---

### 4. Quick Setup Button

**Location:** Project details page

**Features:**
- "Configure Supabase" button if not configured
- "Update Supabase Config" button if configured
- Opens configuration modal

---

### 5. Supabase Dashboard Link

**Location:** Configuration modal/form

**Features:**
- "Get Credentials from Supabase" button
- Opens Supabase dashboard in new tab
- Direct link to Settings > API page

---

## 📝 Frontend Implementation Details

### API Service Functions

```typescript
// services/supabaseApi.ts

// Update Supabase configuration
export async function updateSupabaseConfig(
  projectId: string,
  config: { supabase_url: string; supabase_anon_key: string }
) {
  const response = await fetch(
    `/api/projects/${projectId}/supabase-config`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }
  );
  return response.json();
}

// Get Supabase configuration status
export async function getSupabaseConfigStatus(projectId: string) {
  const response = await fetch(
    `/api/projects/${projectId}/supabase-config`
  );
  return response.json();
}

// Test Supabase connection
export async function testSupabaseConnection(
  projectId: string,
  config: { supabase_url: string; supabase_anon_key: string }
) {
  const response = await fetch(
    `/api/projects/${projectId}/test-supabase`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }
  );
  return response.json();
}
```

---

### React Component Examples

#### 1. Supabase Configuration Modal

```typescript
// components/SupabaseConfigModal.tsx
import React, { useState } from 'react';
import { Modal, Form, Input, Button, Alert } from 'antd';
import { updateSupabaseConfig, testSupabaseConnection } from '../services/supabaseApi';

interface Props {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const SupabaseConfigModal: React.FC<Props> = ({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTest = async () => {
    const values = form.getFieldsValue();
    if (!values.supabase_url || !values.supabase_anon_key) {
      setError('Please fill in both fields');
      return;
    }

    setTesting(true);
    setError(null);
    try {
      const result = await testSupabaseConnection(projectId, {
        supabase_url: values.supabase_url,
        supabase_anon_key: values.supabase_anon_key,
      });
      
      if (result.success) {
        Alert.success('Connection successful!');
      } else {
        setError(result.message || 'Connection failed');
      }
    } catch (err) {
      setError('Failed to test connection');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    const values = form.getFieldsValue();
    setLoading(true);
    setError(null);
    
    try {
      await updateSupabaseConfig(projectId, {
        supabase_url: values.supabase_url,
        supabase_anon_key: values.supabase_anon_key,
      });
      Alert.success('Configuration saved!');
      onSuccess();
      onClose();
    } catch (err) {
      setError('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Configure Supabase"
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      <Form form={form} layout="vertical">
        {error && <Alert message={error} type="error" style={{ marginBottom: 16 }} />}
        
        <Form.Item
          label="Supabase URL"
          name="supabase_url"
          rules={[{ required: true, message: 'Please enter Supabase URL' }]}
        >
          <Input placeholder="https://xxxxx.supabase.co" />
        </Form.Item>

        <Form.Item
          label="Supabase Anon Key"
          name="supabase_anon_key"
          rules={[{ required: true, message: 'Please enter Anon Key' }]}
        >
          <Input.Password placeholder="eyJhbGciOiJIUzI1NiIs..." />
        </Form.Item>

        <div style={{ marginBottom: 16 }}>
          <a
            href="https://app.supabase.com/project/_/settings/api"
            target="_blank"
            rel="noopener noreferrer"
          >
            Get credentials from Supabase Dashboard →
          </a>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <Button onClick={handleTest} loading={testing}>
            Test Connection
          </Button>
          <Button
            type="primary"
            onClick={handleSave}
            loading={loading}
            style={{ flex: 1 }}
          >
            Save Configuration
          </Button>
        </div>
      </Form>
    </Modal>
  );
};
```

---

#### 2. Supabase Status Badge

```typescript
// components/SupabaseStatusBadge.tsx
import React from 'react';
import { Badge, Tooltip } from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

interface Props {
  isConfigured: boolean;
  onClick?: () => void;
}

export const SupabaseStatusBadge: React.FC<Props> = ({
  isConfigured,
  onClick,
}) => {
  if (isConfigured) {
    return (
      <Tooltip title="Supabase is configured">
        <Badge
          status="success"
          text="Supabase Configured"
          style={{ cursor: onClick ? 'pointer' : 'default' }}
          onClick={onClick}
        />
      </Tooltip>
    );
  }

  return (
    <Tooltip title="Click to configure Supabase">
      <Badge
        status="warning"
        text="Supabase Not Configured"
        style={{ cursor: 'pointer' }}
        onClick={onClick}
      />
    </Tooltip>
  );
};
```

---

#### 3. Project Card with Supabase Status

```typescript
// components/ProjectCard.tsx
import React, { useState, useEffect } from 'react';
import { Card, Button } from 'antd';
import { SupabaseStatusBadge } from './SupabaseStatusBadge';
import { SupabaseConfigModal } from './SupabaseConfigModal';
import { getSupabaseConfigStatus } from '../services/supabaseApi';

interface Props {
  project: {
    id: string;
    name: string;
    status: string;
  };
}

export const ProjectCard: React.FC<Props> = ({ project }) => {
  const [supabaseConfigured, setSupabaseConfigured] = useState(false);
  const [configModalOpen, setConfigModalOpen] = useState(false);

  useEffect(() => {
    // Check Supabase status on mount
    getSupabaseConfigStatus(project.id).then((result) => {
      setSupabaseConfigured(result.configured);
    });
  }, [project.id]);

  return (
    <>
      <Card
        title={project.name}
        extra={
          <SupabaseStatusBadge
            isConfigured={supabaseConfigured}
            onClick={() => setConfigModalOpen(true)}
          />
        }
      >
        <p>Status: {project.status}</p>
        <Button onClick={() => setConfigModalOpen(true)}>
          {supabaseConfigured ? 'Update Supabase Config' : 'Configure Supabase'}
        </Button>
      </Card>

      <SupabaseConfigModal
        projectId={project.id}
        isOpen={configModalOpen}
        onClose={() => setConfigModalOpen(false)}
        onSuccess={() => {
          setSupabaseConfigured(true);
        }}
      />
    </>
  );
};
```

---

## 🚀 Integration Flow

### After Project Generation:

1. **Show Success Message**
   - "Project created successfully!"
   - "Configure Supabase authentication?" option

2. **If User Chooses to Configure:**
   - Open Supabase Setup Wizard
   - Guide through steps
   - Save configuration

3. **If User Skips:**
   - Show badge "Supabase Not Configured"
   - Allow configuration later from project page

---

## 📋 Checklist for Frontend Implementation

### API Integration
- [ ] Add `updateSupabaseConfig` API function
- [ ] Add `getSupabaseConfigStatus` API function
- [ ] Add `testSupabaseConnection` API function
- [ ] Handle API errors gracefully

### Components
- [ ] Create `SupabaseConfigModal` component
- [ ] Create `SupabaseStatusBadge` component
- [ ] Create `SupabaseSetupWizard` component (optional)
- [ ] Add Supabase status to project cards
- [ ] Add "Configure Supabase" button to project details

### User Experience
- [ ] Show setup wizard after project generation
- [ ] Show status badge on project cards
- [ ] Add help text/link to Supabase dashboard
- [ ] Show success/error messages
- [ ] Allow configuration update anytime

### Validation
- [ ] Validate URL format
- [ ] Validate key format (JWT)
- [ ] Test connection before saving
- [ ] Show clear error messages

---

## 🔗 Useful Links

- **Supabase Dashboard:** https://app.supabase.com
- **Supabase Docs:** https://supabase.com/docs
- **Get API Keys:** https://app.supabase.com/project/_/settings/api

---

## 📝 Notes

1. **Security:** Supabase Anon Key is safe to use in client-side code
2. **Environment Variables:** Users need to update `.env` and `app.json`
3. **Testing:** Always test connection before saving
4. **User Experience:** Make it easy to find and configure Supabase credentials

