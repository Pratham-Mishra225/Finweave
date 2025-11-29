/**
 * Firebase Configuration and Authentication
 * 
 * Configuration is loaded from environment variables (.env file).
 * Set these in your .env file using EXPO_PUBLIC_ prefix.
 */

import { initializeApp, getApps } from 'firebase/app';
import { 
  initializeAuth,
  getReactNativePersistence,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Firebase configuration from environment variables
// These are loaded from .env file using EXPO_PUBLIC_ prefix
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID
};

// Initialize Firebase only if not already initialized
let app;
if (!getApps().length) {
  app = initializeApp(firebaseConfig);
} else {
  app = getApps()[0];
}

// Initialize Auth with AsyncStorage persistence for React Native
const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage)
});

/**
 * Sign up with email and password
 */
export const signUpWithEmail = async (email, password, displayName) => {
  try {
    console.log('Attempting signup with email:', email);
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    console.log('Firebase signup successful for user:', user.uid);
    
    // Get ID token
    const idToken = await user.getIdToken();
    
    // Store token
    await AsyncStorage.setItem('userToken', idToken);
    await AsyncStorage.setItem('userData', JSON.stringify({
      uid: user.uid,
      email: user.email,
      displayName: displayName
    }));
    
    return { user, idToken };
  } catch (error) {
    console.error('Sign up error:', error);
    console.error('Error code:', error.code);
    console.error('Error message:', error.message);
    
    // Handle specific Firebase errors
    let errorMessage;
    
    switch (error.code) {
      case 'auth/email-already-in-use':
        errorMessage = 'An account with this email already exists.';
        break;
      case 'auth/invalid-email':
        errorMessage = 'Invalid email address.';
        break;
      case 'auth/operation-not-allowed':
        errorMessage = 'Email/password accounts are not enabled.';
        break;
      case 'auth/weak-password':
        errorMessage = 'Password is too weak. Use at least 6 characters.';
        break;
      default:
        errorMessage = error.message || 'Signup failed. Please try again.';
    }
    
    throw new Error(errorMessage);
  }
};

/**
 * Sign in with email and password
 */
export const signInWithEmail = async (email, password) => {
  try {
    console.log('Attempting login with email:', email);
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    console.log('Firebase login successful for user:', user.uid);
    
    // Get ID token
    const idToken = await user.getIdToken();
    
    // Store token
    await AsyncStorage.setItem('userToken', idToken);
    await AsyncStorage.setItem('userData', JSON.stringify({
      uid: user.uid,
      email: user.email,
      displayName: user.displayName
    }));
    
    return { user, idToken };
  } catch (error) {
    console.error('Sign in error:', error);
    console.error('Error code:', error.code);
    console.error('Error message:', error.message);
    
    // Handle specific Firebase errors
    let errorMessage;
    
    switch (error.code) {
      case 'auth/invalid-email':
        errorMessage = 'Invalid email address.';
        break;
      case 'auth/user-disabled':
        errorMessage = 'This account has been disabled.';
        break;
      case 'auth/user-not-found':
        errorMessage = 'No account found with this email.';
        break;
      case 'auth/wrong-password':
        errorMessage = 'Incorrect password.';
        break;
      case 'auth/invalid-credential':
        errorMessage = 'Invalid email or password.';
        break;
      case 'auth/too-many-requests':
        errorMessage = 'Too many failed attempts. Please try again later.';
        break;
      default:
        errorMessage = error.message || 'Login failed. Please try again.';
    }
    
    throw new Error(errorMessage);
  }
};

/**
 * Sign in with Google - React Native Compatible
 * For full Google Sign-In, expo-auth-session setup is required
 */
export const signInWithGoogle = async () => {
  try {
    // Google Sign-In requires expo-auth-session for React Native
    throw new Error('Google Sign-In requires expo-auth-session setup. Please use email/password for now.');
  } catch (error) {
    console.error('Google sign in error:', error);
    throw error;
  }
};

/**
 * Sign out
 */
export const signOutUser = async () => {
  try {
    await signOut(auth);
    await AsyncStorage.removeItem('userToken');
    await AsyncStorage.removeItem('userData');
  } catch (error) {
    console.error('Sign out error:', error);
    throw error;
  }
};

/**
 * Get current user's ID token
 */
export const getCurrentUserToken = async () => {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  return null;
};

/**
 * Refresh ID token
 */
export const refreshUserToken = async () => {
  const user = auth.currentUser;
  if (user) {
    const newToken = await user.getIdToken(true); // Force refresh
    await AsyncStorage.setItem('userToken', newToken);
    return newToken;
  }
  return null;
};

/**
 * Auth state change listener
 */
export const onAuthChange = (callback) => {
  return onAuthStateChanged(auth, callback);
};

/**
 * Get stored token from AsyncStorage
 */
export const getStoredToken = async () => {
  try {
    return await AsyncStorage.getItem('userToken');
  } catch (error) {
    console.error('Error getting stored token:', error);
    return null;
  }
};

/**
 * Get stored user data from AsyncStorage
 */
export const getStoredUserData = async () => {
  try {
    const userData = await AsyncStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
  } catch (error) {
    console.error('Error getting stored user data:', error);
    return null;
  }
};

/**
 * Backend API Configuration
 * 
 * The backend URL is read from environment variables (.env file).
 * Use EXPO_PUBLIC_ prefix to make it available to the app.
 */
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// Set to true to enable debug logging
const DEBUG_MODE = process.env.EXPO_PUBLIC_DEBUG_MODE === 'true';

/**
 * Verify token with backend
 */
export const verifyTokenWithBackend = async (token) => {
  try {
    if (DEBUG_MODE) {
      console.log(`Connecting to backend at: ${BACKEND_URL}`);
      console.log('Token (first 50 chars):', token.substring(0, 50));
    }
    
    const response = await fetch(`${BACKEND_URL}/auth/login/verify-token`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (DEBUG_MODE) {
      console.log('Backend response status:', response.status);
    }
    
    if (!response.ok) {
      let userMessage = 'Authentication failed. Please try logging in again.';
      switch (response.status) {
        case 401:
          userMessage = 'Your session has expired. Please log in again.';
          break;
        case 403:
          userMessage = 'Access denied. Please check your credentials.';
          break;
        case 500:
          userMessage = 'Server error. Please try again later.';
          break;
      }
      if (DEBUG_MODE) {
        const errorText = await response.text();
        console.error('Backend error response:', errorText);
        console.error('Response status:', response.status, response.statusText);
      }
      throw new Error(userMessage);
    }
    
    const data = await response.json();
    if (DEBUG_MODE) {
      console.log('Backend verification successful:', data);
    }
    return data;
  } catch (error) {
    if (DEBUG_MODE) {
      console.error('Backend verification error:', error);
    }
    throw error;
  }
};

export { auth };
