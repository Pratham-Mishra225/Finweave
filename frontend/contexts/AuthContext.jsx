/**
 * Authentication Context Provider
 * 
 * Manages global authentication state and provides auth methods
 * to all components in the app.
 */

import React, { createContext, useState, useEffect, useContext } from 'react';
import { 
  onAuthChange, 
  signInWithEmail, 
  signUpWithEmail, 
  signInWithGoogle,
  signOutUser,
  getStoredToken,
  getStoredUserData,
  verifyTokenWithBackend,
  getCurrentUserToken
} from '../config/firebase';

const AuthContext = createContext({});

/**
 * Helper function to transform Firebase user data
 */
const transformFirebaseUser = (firebaseUser, displayName = null) => ({
  uid: firebaseUser.uid,
  email: firebaseUser.email,
  displayName: displayName || firebaseUser.displayName,
  photoURL: firebaseUser.photoURL,
  emailVerified: firebaseUser.emailVerified
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [idToken, setIdToken] = useState(null);

  // Initialize auth state on app load
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check for stored token
        const storedToken = await getStoredToken();
        const storedUser = await getStoredUserData();
        
        if (storedToken && storedUser) {
          // Verify token with backend
          try {
            await verifyTokenWithBackend(storedToken);
            setUser(storedUser);
            setIdToken(storedToken);
          } catch (error) {
            console.error('Token verification failed:', error);
            // Clear invalid token
            await signOutUser();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    // Listen for auth state changes
    const unsubscribe = onAuthChange(async (firebaseUser) => {
      if (firebaseUser) {
        const token = await firebaseUser.getIdToken();
        const userData = transformFirebaseUser(firebaseUser);
        
        setUser(userData);
        setIdToken(token);
        setLoading(false);
      } else {
        setUser(null);
        setIdToken(null);
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  /**
   * Sign up with email and password
   */
  const signUp = async (email, password, displayName) => {
    try {
      setError(null);
      setLoading(true);
      
      const { user: firebaseUser, idToken: token } = await signUpWithEmail(
        email, 
        password, 
        displayName
      );
      
      // Verify with backend
      await verifyTokenWithBackend(token);
      
      const userData = transformFirebaseUser(firebaseUser, displayName);
      
      setUser(userData);
      setIdToken(token);
      
      return { success: true, user: userData };
    } catch (err) {
      setError(err.message);
      console.error('Sign up error:', err);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign in with email and password
   */
  const signIn = async (email, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const { user: firebaseUser, idToken: token } = await signInWithEmail(
        email, 
        password
      );
      
      // Verify with backend
      await verifyTokenWithBackend(token);
      
      const userData = transformFirebaseUser(firebaseUser);
      
      setUser(userData);
      setIdToken(token);
      
      return { success: true, user: userData };
    } catch (err) {
      setError(err.message);
      console.error('Sign in error:', err);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign in with Google
   */
  const signInGoogle = async () => {
    try {
      setError(null);
      setLoading(true);
      
      const { user: firebaseUser, idToken: token } = await signInWithGoogle();
      
      // Verify with backend (creates user if doesn't exist)
      await verifyTokenWithBackend(token);
      
      const userData = transformFirebaseUser(firebaseUser);
      
      setUser(userData);
      setIdToken(token);
      
      return { success: true, user: userData };
    } catch (err) {
      setError(err.message);
      console.error('Google sign in error:', err);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign out
   */
  const signOut = async () => {
    try {
      setError(null);
      await signOutUser();
      setUser(null);
      setIdToken(null);
      return { success: true };
    } catch (err) {
      setError(err.message);
      console.error('Sign out error:', err);
      return { success: false, error: err.message };
    }
  };

  /**
   * Get fresh ID token
   */
  const getToken = async () => {
    try {
      const token = await getCurrentUserToken();
      if (token) {
        setIdToken(token);
        return token;
      }
      return null;
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  };

  const value = {
    user,
    loading,
    error,
    idToken,
    signUp,
    signIn,
    signInGoogle,
    signOut,
    getToken,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
