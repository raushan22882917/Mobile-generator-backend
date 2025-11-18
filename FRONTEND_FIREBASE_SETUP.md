# Frontend Firebase Setup Guide

This guide shows you how to set up Firebase Authentication in your frontend application.

## Quick Start

### Option 1: Use Backend API Only (Recommended - No Firebase SDK Required)

You can use the backend API directly without installing Firebase SDK:

```javascript
// Login example
const login = async (email, password) => {
  const response = await fetch('https://your-backend.com/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Store token
    localStorage.setItem('authToken', data.token);
    // Store user info
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }
  
  throw new Error(data.message);
};

// Signup example
const signup = async (email, password, name) => {
  const response = await fetch('https://your-backend.com/auth/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password, name }),
  });
  
  const data = await response.json();
  return data;
};

// Make authenticated requests
const makeAuthenticatedRequest = async (url, options = {}) => {
  const token = localStorage.getItem('authToken');
  
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

### Option 2: Use Firebase SDK (For Advanced Features)

If you want to use Firebase SDK for additional features (like real-time auth state, social login, etc.):

#### 1. Install Firebase SDK

```bash
npm install firebase
```

#### 2. Create Firebase Config File

Create `firebase-config.js` (or `firebase-config.ts` for TypeScript):

```javascript
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyAN5hfhAjpLOy7I9nPZiZeolFtCUT7PQ3g",
  authDomain: "gen-lang-client-0148980288.firebaseapp.com",
  projectId: "gen-lang-client-0148980288",
  storageBucket: "gen-lang-client-0148980288.firebasestorage.app",
  messagingSenderId: "1098053868371",
  appId: "1:1098053868371:web:fa27fa17ddae90f2081fa6",
  measurementId: "G-2S2JEE401K"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const analytics = getAnalytics(app);
export default app;
```

#### 3. Use Firebase Auth

```javascript
import { auth } from './firebase-config';
import { 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';

// Sign up
const signup = async (email, password) => {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password);
  const idToken = await userCredential.user.getIdToken();
  
  // Verify with backend
  const response = await fetch('https://your-backend.com/auth/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  
  return response.json();
};

// Sign in
const login = async (email, password) => {
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  const idToken = await userCredential.user.getIdToken();
  
  // Verify with backend
  const response = await fetch('https://your-backend.com/auth/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  
  return response.json();
};

// Sign out
const logout = async () => {
  await signOut(auth);
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
};

// Listen to auth state changes
onAuthStateChanged(auth, async (user) => {
  if (user) {
    const idToken = await user.getIdToken();
    localStorage.setItem('authToken', idToken);
  } else {
    localStorage.removeItem('authToken');
  }
});
```

## Your Firebase Configuration

Your Firebase project is already configured:
- **Project ID:** `gen-lang-client-0148980288`
- **API Key:** `AIzaSyAN5hfhAjpLOy7I9nPZiZeolFtCUT7PQ3g`
- **Auth Domain:** `gen-lang-client-0148980288.firebaseapp.com`

## Backend API Key

For backend authentication, use this API key in your `.env` file:

```env
FIREBASE_API_KEY=AIzaSyAN5hfhAjpLOy7I9nPZiZeolFtCUT7PQ3g
```

This is the same API key from your Firebase config, and it's already set as the default in `config.py`.

## Recommendation

**Use Option 1 (Backend API Only)** because:
- ✅ Simpler - no Firebase SDK installation
- ✅ Smaller bundle size
- ✅ Works with any frontend framework
- ✅ All authentication handled by backend
- ✅ Token management is straightforward

Use Option 2 (Firebase SDK) only if you need:
- Real-time auth state listeners
- Social login (Google, Facebook, etc.)
- Phone authentication
- Other Firebase features

## Next Steps

1. **For Backend API Only:**
   - Use the login/signup examples above
   - Store the token from `/auth/login` response
   - Include token in `Authorization: Bearer <token>` header

2. **For Firebase SDK:**
   - Install Firebase: `npm install firebase`
   - Copy the config file provided
   - Use Firebase Auth functions
   - Call `/auth/verify` after authentication

## Security Note

⚠️ **Important:** The Firebase config (including API key) is safe to expose in frontend code. Firebase API keys are public and are meant to be included in client-side code. They are restricted by domain/app ID in Firebase Console.

However, keep your Firebase Admin SDK credentials (service account key) secret - those should only be on the backend.

