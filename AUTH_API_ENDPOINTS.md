# Authentication API Endpoints

This document lists all authentication-related API endpoints available in the backend.

## Overview

The backend uses Firebase Authentication. All authentication endpoints work with Firebase ID tokens.

## Authentication Endpoints

### 1. POST `/auth/signup`

**Purpose:** Register a new user account using Firebase Admin SDK

**Description:**
- Creates a new user account in Firebase Auth
- This endpoint allows the backend to create users programmatically
- Note: Typically, users sign up on the frontend using Firebase Auth SDK, but this endpoint provides backend user creation capability

**Request:**
- **Method:** `POST`
- **URL:** `/auth/signup`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "User Name"  // Optional
  }
  ```

**Response (Success - 201 Created):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "token": null,
  "user": {
    "id": "firebase-uid",
    "email": "user@example.com",
    "name": "User Name",
    "created_at": "2024-01-01T00:00:00",
    "last_login": null,
    "is_active": true
  }
}
```

**Response (Error - 400 Bad Request):**
```json
{
  "success": false,
  "message": "Failed to create user. Email may already exist or password is too weak."
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "success": false,
  "message": "Authentication service not initialized"
}
```
or
```json
{
  "success": false,
  "message": "Failed to create user account"
}
```

**Usage:**
1. Frontend sends email, password, and optional name to this endpoint
2. Backend creates user in Firebase Auth
3. User needs to sign in (using Firebase Auth SDK on frontend) to get ID token
4. After sign in, use `/auth/verify` to verify token and get user info

**Note:** After signup, the user should sign in using Firebase Auth SDK on the frontend to get an ID token, then call `/auth/verify` to complete authentication.

---

### 2. POST `/auth/login`

**Purpose:** Check if user exists and is active (for login flow)

**Description:**
- Checks if user exists in Firebase Auth
- Verifies user account is active
- **Important:** Firebase requires password verification to happen client-side for security
- This endpoint confirms user exists, but actual authentication must use Firebase Auth SDK on frontend

**Request:**
- **Method:** `POST`
- **URL:** `/auth/login`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "User found. Please use Firebase Auth SDK on frontend to sign in and get ID token, then call /auth/verify",
  "token": null,
  "user": {
    "id": "firebase-uid",
    "email": "user@example.com",
    "name": "User Name",
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-01-01T00:00:00",
    "is_active": true
  }
}
```

**Response (Error - 401 Unauthorized):**
```json
{
  "success": false,
  "message": "Invalid email or password"
}
```
or
```json
{
  "success": false,
  "message": "User account is disabled"
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "success": false,
  "message": "Authentication service not initialized"
}
```
or
```json
{
  "success": false,
  "message": "Login failed"
}
```

**Usage:**
1. Frontend sends email and password to this endpoint
2. Backend checks if user exists and is active
3. **Frontend must then use Firebase Auth SDK** to actually authenticate:
   ```javascript
   const { user } = await signInWithEmailAndPassword(auth, email, password);
   const idToken = await user.getIdToken();
   ```
4. Call `/auth/verify` with the ID token to complete authentication

**Note:** This endpoint only verifies user existence. Actual password verification and token generation must happen on the frontend using Firebase Auth SDK for security reasons.

---

### 3. POST `/auth/verify`

**Purpose:** Verify Firebase ID token and get user information

**Description:**
- Validates a Firebase ID token sent from the frontend
- Returns user information if token is valid
- This endpoint should be called after the user authenticates with Firebase on the frontend

**Request:**
- **Method:** `POST`
- **URL:** `/auth/verify`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body:**
  ```json
  {
    "id_token": "firebase-id-token-here"
  }
  ```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Token verified successfully",
  "token": "firebase-id-token",
  "user": {
    "id": "firebase-uid",
    "email": "user@example.com",
    "name": "User Name",
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-01-01T00:00:00",
    "is_active": true
  }
}
```

**Response (Error - 401 Unauthorized):**
```json
{
  "success": false,
  "message": "Invalid or expired Firebase ID token"
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "success": false,
  "message": "Authentication service not initialized"
}
```
or
```json
{
  "success": false,
  "message": "Token verification failed"
}
```

**Usage:**
1. User authenticates with Firebase on frontend (email/password, Google, etc.)
2. Frontend gets Firebase ID token using `auth.currentUser.getIdToken()`
3. Frontend sends token to this endpoint
4. Backend verifies token and returns user information
5. Frontend stores user info in app state

---

### 4. GET `/auth/me`

**Purpose:** Get current authenticated user information

**Description:**
- Returns the profile of the currently authenticated user
- Requires a valid Firebase ID token in the Authorization header
- Used to check if user is logged in and get their details

**Request:**
- **Method:** `GET`
- **URL:** `/auth/me`
- **Headers:**
  ```
  Authorization: Bearer <firebase-id-token>
  ```

**Response (Success - 200):**
```json
{
  "id": "firebase-uid",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T00:00:00"
}
```

**Response (Error - 401 Unauthorized):**
```json
{
  "detail": "Missing authorization header"
}
```
or
```json
{
  "detail": "Invalid authorization header format. Expected: Bearer <token>"
}
```
or
```json
{
  "detail": "Invalid or expired token"
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "detail": "Authentication service not initialized"
}
```

**Usage:**
1. Frontend includes Firebase ID token in Authorization header
2. Backend verifies token and returns user information
3. Frontend can use this to:
   - Check if user is authenticated
   - Display user profile
   - Get user ID for API calls

---

## Request/Response Models

### SignupRequest
```typescript
{
  email: string        // User email address (min 5 characters)
  password: string     // User password (min 6 characters)
  name?: string        // Optional user display name
}
```

### LoginRequest
```typescript
{
  email: string     // User email address
  password: string  // User password
}
```

### VerifyTokenRequest
```typescript
{
  id_token: string  // Firebase ID token to verify
}
```

### AuthResponse
```typescript
{
  success: boolean
  message: string
  token?: string  // Firebase ID token (same as sent)
  user?: {
    id: string
    email: string
    name?: string
    created_at: string
    last_login?: string
    is_active: boolean
  }
}
```

### UserResponse
```typescript
{
  id: string
  email: string
  name?: string
  created_at: string
  last_login?: string
}
```

---

## Authentication Flow

### Option 1: Frontend Signup (Recommended)

1. **Frontend: User Signs Up**
   - User enters credentials on frontend
   - Frontend uses Firebase Auth SDK: `createUserWithEmailAndPassword()`
   - User is automatically signed in
   - Frontend gets Firebase ID token: `auth.currentUser.getIdToken()`

2. **Frontend: Verify Token with Backend**
   - Call `POST /auth/verify` with the Firebase ID token
   - Backend verifies token and returns user info
   - Frontend stores user info in app state/context

3. **Frontend: Make Authenticated Requests**
   - Include Firebase ID token in `Authorization: Bearer <token>` header
   - Use for all protected endpoints

### Option 2: Backend Signup

1. **Backend: Create User**
   - Call `POST /auth/signup` with email, password, and optional name
   - Backend creates user in Firebase Auth
   - Returns user information (no token yet)

2. **Frontend: User Signs In**
   - User signs in using Firebase Auth SDK: `signInWithEmailAndPassword()`
   - Frontend gets Firebase ID token: `auth.currentUser.getIdToken()`

3. **Frontend: Verify Token with Backend**
   - Call `POST /auth/verify` with the Firebase ID token
   - Backend verifies token and returns user info
   - Frontend stores user info in app state/context

4. **Frontend: Make Authenticated Requests**
   - Include Firebase ID token in `Authorization: Bearer <token>` header
   - Use for all protected endpoints

### Option 3: Backend Login Check (Optional)

1. **Backend: Check User Exists**
   - Call `POST /auth/login` with email and password
   - Backend verifies user exists and is active
   - Returns user information (no token yet)

2. **Frontend: Authenticate with Firebase**
   - Use Firebase Auth SDK: `signInWithEmailAndPassword(email, password)`
   - Get Firebase ID token: `auth.currentUser.getIdToken()`

3. **Frontend: Verify Token with Backend**
   - Call `POST /auth/verify` with the Firebase ID token
   - Backend verifies token and returns user info
   - Frontend stores user info in app state/context

4. **Frontend: Make Authenticated Requests**
   - Include Firebase ID token in `Authorization: Bearer <token>` header
   - Use for all protected endpoints

### Complete Authentication Flow (After Signup):

1. **Frontend: User Signs In**
   - User enters credentials (email/password, Google, etc.)
   - Firebase Auth handles authentication
   - Frontend gets Firebase ID token: `auth.currentUser.getIdToken()`

2. **Frontend: Verify Token with Backend**
   - Call `POST /auth/verify` with the Firebase ID token
   - Backend verifies token and returns user info
   - Frontend stores user info in app state/context

3. **Frontend: Make Authenticated Requests**
   - Include Firebase ID token in `Authorization: Bearer <token>` header
   - Use for all protected endpoints (e.g., `GET /auth/me`, `POST /generate`, etc.)

4. **Token Refresh**
   - Firebase tokens expire after 1 hour
   - Use `onIdTokenChanged()` listener to auto-refresh
   - Or manually refresh: `auth.currentUser.getIdToken(true)`
   - Update stored token when it changes

---

## Protected Endpoints

All endpoints that require authentication use the `get_current_user` dependency, which expects:
- **Header:** `Authorization: Bearer <firebase-id-token>`

Examples of protected endpoints:
- `GET /auth/me` - Get current user
- `POST /generate` - Generate new project
- `GET /status/{project_id}` - Get project status
- `GET /projects` - List user's projects
- `GET /files/{project_id}` - Get project files
- And many more...

---

## Error Handling

### Common Error Codes:

- **401 Unauthorized**
  - Missing Authorization header
  - Invalid token format
  - Expired or invalid token
  - **Solution:** Refresh token and retry

- **403 Forbidden**
  - Token is valid but user doesn't have access to the resource
  - **Solution:** Check user permissions

- **500 Internal Server Error**
  - Authentication service not initialized
  - Backend error
  - **Solution:** Contact support or check backend logs

---

## Example Frontend Usage

### JavaScript/TypeScript Example:

```javascript
// After Firebase authentication
const idToken = await auth.currentUser.getIdToken();

// Verify token with backend
const verifyResponse = await fetch('https://your-backend.com/auth/verify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ id_token: idToken })
});

const { success, user, token } = await verifyResponse.json();

if (success) {
  // Store user info
  setUser(user);
  setAuthToken(token);
}

// Make authenticated request
const meResponse = await fetch('https://your-backend.com/auth/me', {
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});

const userInfo = await meResponse.json();
```

---

## Related Documentation

For detailed frontend integration guide, see: [FIREBASE_AUTH_FRONTEND_GUIDE.md](./FIREBASE_AUTH_FRONTEND_GUIDE.md)

