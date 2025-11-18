// Firebase Configuration (TypeScript)
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics, Analytics } from "firebase/analytics";
import { getAuth, Auth } from "firebase/auth";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAN5hfhAjpLOy7I9nPZiZeolFtCUT7PQ3g",
  authDomain: "gen-lang-client-0148980288.firebaseapp.com",
  projectId: "gen-lang-client-0148980288",
  storageBucket: "gen-lang-client-0148980288.firebasestorage.app",
  messagingSenderId: "1098053868371",
  appId: "1:1098053868371:web:fa27fa17ddae90f2081fa6",
  measurementId: "G-2S2JEE401K"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Analytics (optional)
const analytics: Analytics = getAnalytics(app);

// Initialize Firebase Auth
export const auth: Auth = getAuth(app);

// Export app for use in other files
export default app;

