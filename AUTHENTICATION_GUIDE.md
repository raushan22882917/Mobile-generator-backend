# Authentication System Guide

## Overview
The backend now includes a complete JWT-based authentication system that allows users to:
- Register new accounts (signup)
- Login with email and password
- Access only their own projects
- Secure API endpoints with JWT tokens

---

## 🔐 Authentication Endpoints

### 1. Signup (Register)
**Endpoint:** `POST /auth/signup`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00",
    "last_login": null,
    "is_active": true
  }
}
```

**Errors:**
- `400`: Email already registered or password too short
- `500`: Server error

---

### 2. Login
**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00",
    "last_login": "2024-01-01T12:00:00",
    "is_active": true
  }
}
```

**Errors:**
- `401`: Invalid email or password
- `500`: Server error

---

### 3. Get Current User
**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T12:00:00",
  "last_login": "2024-01-01T12:00:00"
}
```

**Errors:**
- `401`: Missing or invalid token

---

## 🔒 Protected Endpoints

All project-related endpoints now require authentication and filter by user:

### Protected Endpoints:
- `POST /generate` - Create new project (uses authenticated user's ID)
- `GET /projects` - List user's projects only
- `GET /status/{project_id}` - Get project status (user's projects only)
- `GET /download/{project_id}` - Download project (user's projects only)
- `GET /files/{project_id}` - Get project files (user's projects only)
- `PUT /files/{project_id}/{file_path}` - Update file (user's projects only)
- `POST /files/{project_id}` - Create file (user's projects only)
- `DELETE /files/{project_id}/{file_path}` - Delete file (user's projects only)
- All Supabase configuration endpoints

### How to Use:
1. **Signup/Login** to get JWT token
2. **Include token** in all requests:
   ```
   Authorization: Bearer <your_jwt_token>
   ```
3. **Access only your projects** - API automatically filters

---

## 📝 Frontend Implementation

### 1. Authentication Service

```typescript
// services/authApi.ts

const API_BASE = 'http://your-api-url';

export async function signup(email: string, password: string, name?: string) {
  const response = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  return response.json();
}

export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

export async function getCurrentUser(token: string) {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return response.json();
}
```

---

### 2. Token Storage

```typescript
// Store token in localStorage or secure storage
localStorage.setItem('auth_token', token);

// Include in all API requests
const token = localStorage.getItem('auth_token');
fetch(`${API_BASE}/projects`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

---

### 3. Login Component Example

```typescript
// components/LoginForm.tsx
import React, { useState } from 'react';
import { login } from '../services/authApi';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await login(email, password);
      
      if (result.success) {
        // Store token
        localStorage.setItem('auth_token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Redirect to projects page
        window.location.href = '/projects';
      } else {
        setError(result.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

### 4. Protected Route Component

```typescript
// components/ProtectedRoute.tsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../services/authApi';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      navigate('/login');
      return;
    }

    // Verify token is valid
    getCurrentUser(token)
      .then(() => {
        setAuthenticated(true);
      })
      .catch(() => {
        localStorage.removeItem('auth_token');
        navigate('/login');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!authenticated) {
    return null;
  }

  return <>{children}</>;
}
```

---

### 5. API Client with Auth

```typescript
// services/apiClient.ts

const API_BASE = 'http://your-api-url';

function getAuthHeaders() {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    // Token expired or invalid
    localStorage.removeItem('auth_token');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  return response.json();
}

// Usage:
export async function getProjects() {
  return apiRequest('/projects');
}

export async function generateProject(prompt: string) {
  return apiRequest('/generate', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  });
}
```

---

## 🔄 User Flow

### Registration Flow:
1. User fills signup form
2. Frontend calls `POST /auth/signup`
3. Backend creates user, returns JWT token
4. Frontend stores token
5. User redirected to projects page

### Login Flow:
1. User fills login form
2. Frontend calls `POST /auth/login`
3. Backend validates credentials, returns JWT token
4. Frontend stores token
5. User redirected to projects page

### Project Access Flow:
1. User requests projects: `GET /projects`
2. Backend verifies JWT token
3. Backend filters projects by `user_id`
4. Returns only user's projects
5. Frontend displays user's projects

---

## 🛡️ Security Features

1. **Password Hashing**: Passwords are hashed with SHA-256 + salt
2. **JWT Tokens**: Secure token-based authentication
3. **Token Expiration**: Tokens expire after 7 days
4. **User Isolation**: Users can only access their own projects
5. **Input Validation**: Email and password validation
6. **Error Handling**: Secure error messages (no password leaks)

---

## 📋 Configuration

### Environment Variables:
```bash
# JWT Secret Key (REQUIRED in production)
JWT_SECRET_KEY=your-very-secure-secret-key-change-this

# User storage directory (optional)
# Default: {projects_base_dir}/users
```

### User Storage:
- Users are stored in: `{projects_base_dir}/users/users.json`
- Format: JSON file with user data
- Passwords are hashed (never stored in plain text)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set JWT Secret Key
```bash
export JWT_SECRET_KEY="your-secure-secret-key"
```

### 3. Start Server
```bash
uvicorn main:app --reload
```

### 4. Test Authentication
```bash
# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get Projects (with token)
curl -X GET http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ✅ Features Implemented

- [x] User registration (signup)
- [x] User login
- [x] JWT token generation
- [x] JWT token validation
- [x] Password hashing
- [x] User data persistence
- [x] Protected endpoints
- [x] User-specific project filtering
- [x] Get current user endpoint
- [x] Secure error handling

---

## 📝 Notes

1. **JWT Secret Key**: Change `JWT_SECRET_KEY` in production!
2. **Password Requirements**: Minimum 6 characters
3. **Token Expiration**: 7 days (configurable in `auth_service.py`)
4. **User Storage**: JSON file (can be migrated to database later)
5. **Backward Compatibility**: Old projects without `user_id` won't appear in authenticated user's list

---

## 🔧 Migration Notes

For existing projects:
- Projects created before authentication will have `user_id="anonymous"`
- These won't appear in authenticated user's project list
- To migrate: Update project metadata files with proper `user_id`

