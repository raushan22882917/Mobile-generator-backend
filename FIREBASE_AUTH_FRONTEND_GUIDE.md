# Firebase Authentication Frontend Integration Guide

This guide explains how to integrate Firebase Authentication in your frontend application to work with this backend API.

## Overview

The backend uses Firebase Admin SDK to verify Firebase ID tokens. Your frontend needs to:
1. Authenticate users using Firebase Auth SDK
2. Get the Firebase ID token after authentication
3. Send the token in API requests to the backend
4. Handle token refresh when it expires

## Step-by-Step Integration

### Step 1: Install Firebase SDK

Install the Firebase JavaScript SDK in your frontend project:

**For React/Next.js:**
```bash
npm install firebase
# or
yarn add firebase
```

**For Vue.js:**
```bash
npm install firebase
```

**For Angular:**
```bash
npm install firebase @angular/fire
```

### Step 2: Get Firebase Configuration

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings (gear icon)
4. Scroll down to "Your apps" section
5. Click on the web app icon (`</>`) or "Add app" if you haven't created one
6. Copy the Firebase configuration object (it looks like this):
   ```javascript
   {
     apiKey: "your-api-key",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "123456789",
     appId: "your-app-id"
   }
   ```

### Step 3: Initialize Firebase in Your App

Create a Firebase configuration file (e.g., `firebase.js` or `firebaseConfig.js`) and initialize Firebase:

**Key points:**
- Import `initializeApp` and `getAuth` from Firebase
- Initialize the app with your config
- Export the auth instance for use throughout your app

### Step 4: Enable Authentication Methods

In Firebase Console:
1. Go to Authentication → Sign-in method
2. Enable the authentication providers you want to use:
   - **Email/Password** (most common)
   - **Google Sign-In**
   - **Facebook**
   - **GitHub**
   - **Phone** (for SMS verification)
   - Any other providers you need

### Step 5: Implement Sign Up

**For Email/Password:**
- Use `createUserWithEmailAndPassword()` function
- Handle success: User is automatically signed in
- Handle errors: Email already exists, weak password, etc.
- After successful signup, get the ID token

**For Google Sign-In:**
- Use `signInWithPopup()` or `signInWithRedirect()` with Google provider
- Handle the authentication result
- Get the ID token after successful sign-in

### Step 6: Implement Sign In

**For Email/Password:**
- Use `signInWithEmailAndPassword()` function
- Handle success: User is authenticated
- Handle errors: Wrong password, user not found, etc.
- Get the ID token after successful sign-in

**For other providers:**
- Use the appropriate sign-in method for each provider
- Always get the ID token after authentication

### Step 7: Get Firebase ID Token

After any successful authentication:
- Call `auth.currentUser.getIdToken()` to get the ID token
- This token is what you'll send to your backend
- Store it securely (in memory, not localStorage for security)

**Important:**
- The token expires after 1 hour
- You need to refresh it periodically
- Use `onIdTokenChanged()` listener to automatically refresh tokens

### Step 8: Send Token to Backend

**For the `/auth/verify` endpoint:**
- After user signs in, call your backend's `/auth/verify` endpoint
- Send the Firebase ID token in the request body:
  ```json
  {
    "id_token": "your-firebase-id-token"
  }
  ```
- Store the response (user info) in your app state

**For protected API endpoints:**
- Include the Firebase ID token in the `Authorization` header:
  ```
  Authorization: Bearer <firebase-id-token>
  ```
- Do this for all requests to protected endpoints

### Step 9: Handle Token Refresh

**Automatic refresh:**
- Use Firebase's `onIdTokenChanged()` listener
- This automatically refreshes tokens when they're about to expire
- Update your stored token when it changes

**Manual refresh:**
- Call `auth.currentUser.getIdToken(true)` to force refresh
- Do this before making important API calls if token might be expired

### Step 10: Implement Sign Out

- Use `signOut()` function from Firebase Auth
- Clear any stored user data and tokens
- Redirect to login page

### Step 11: Check Authentication State

**On app load:**
- Use `onAuthStateChanged()` listener to check if user is logged in
- This fires when:
  - App loads (checks current auth state)
  - User signs in
  - User signs out
  - Token changes

**Use this to:**
- Show/hide login UI
- Redirect to appropriate pages
- Initialize user data

### Step 12: Handle Protected Routes

**In your routing:**
- Check if user is authenticated before allowing access
- Redirect to login if not authenticated
- Show loading state while checking auth

**For React Router:**
- Create a ProtectedRoute component
- Check auth state before rendering
- Redirect to login if needed

**For Next.js:**
- Use middleware or getServerSideProps to check auth
- Or use client-side checks in useEffect

### Step 13: Error Handling

**Common errors to handle:**
- `auth/user-not-found` - User doesn't exist
- `auth/wrong-password` - Incorrect password
- `auth/email-already-in-use` - Email already registered
- `auth/weak-password` - Password too weak
- `auth/invalid-email` - Invalid email format
- `auth/network-request-failed` - Network error
- `auth/too-many-requests` - Too many failed attempts

**Backend errors:**
- 401 Unauthorized - Token invalid or expired (refresh token)
- 500 Server Error - Backend issue (show error message)

### Step 14: Security Best Practices

1. **Never store tokens in localStorage** - Use memory or secure storage
2. **Always use HTTPS** - Firebase requires HTTPS in production
3. **Validate email** - Use Firebase's email verification if needed
4. **Handle token expiration** - Always check and refresh tokens
5. **Secure API calls** - Always include token in Authorization header
6. **Logout on errors** - If token verification fails, sign out user

### Step 15: Testing Your Integration

**Test scenarios:**
1. Sign up with new email/password
2. Sign in with existing credentials
3. Sign in with Google (or other provider)
4. Access protected route while logged in
5. Access protected route while logged out (should redirect)
6. Make API call with valid token
7. Make API call with expired token (should refresh)
8. Sign out and verify token is cleared

## API Endpoints Reference

### POST `/auth/verify`
- **Purpose:** Verify Firebase ID token and get user info
- **Request Body:**
  ```json
  {
    "id_token": "firebase-id-token-here"
  }
  ```
- **Response:**
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
      "last_login": "2024-01-01T00:00:00"
    }
  }
  ```

### GET `/auth/me`
- **Purpose:** Get current authenticated user info
- **Headers:** `Authorization: Bearer <firebase-id-token>`
- **Response:** User object (same as above)

### All Protected Endpoints
- **Headers:** `Authorization: Bearer <firebase-id-token>`
- **Behavior:** Returns 401 if token is invalid or missing

## Common Implementation Patterns

### Pattern 1: Auth Context/Provider (React)
- Create an AuthContext to share auth state
- Provide auth methods (signIn, signOut, etc.)
- Use throughout your app with useContext

### Pattern 2: Auth Store (State Management)
- Use Redux, Zustand, or similar
- Store user data and auth state
- Create actions for auth operations

### Pattern 3: Auth Hook (Custom Hook)
- Create useAuth() hook
- Encapsulate all auth logic
- Return user, loading, error, and auth methods

### Pattern 4: API Client Wrapper
- Create an API client that automatically adds Authorization header
- Handle token refresh automatically
- Retry requests with new token if 401 error

## Troubleshooting

### Token not working
- Check if token is being sent correctly in header
- Verify token hasn't expired (refresh it)
- Check Firebase project configuration matches backend

### CORS errors
- Ensure backend CORS is configured to allow your frontend domain
- Check if Authorization header is allowed

### User not found errors
- Verify user exists in Firebase Auth
- Check if email is verified (if email verification is required)

### Token refresh issues
- Ensure onIdTokenChanged listener is set up
- Check network connectivity
- Verify Firebase project is active

## Next Steps

1. Set up Firebase project and get configuration
2. Install Firebase SDK in your frontend
3. Implement basic sign up/sign in
4. Integrate with backend `/auth/verify` endpoint
5. Add token to API requests
6. Implement protected routes
7. Add error handling and loading states
8. Test all authentication flows

## Additional Resources

- [Firebase Auth Documentation](https://firebase.google.com/docs/auth)
- [Firebase Web SDK Reference](https://firebase.google.com/docs/reference/js)
- [Firebase Auth Best Practices](https://firebase.google.com/docs/auth/web/best-practices)

