import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// API base URL - matches the apiClient configuration which includes /api
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// API interfaces
interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  created_at: string;
}

interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthResponse {
  success: boolean;
  message: string;
  data: {
    user: User;
    tokens: AuthTokens;
  };
}

// Auth context type
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  error: string | null;
  clearError: () => void;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  // Initialize authentication state on app load
  useEffect(() => {
    initializeAuth();
  }, []);

  // Set up automatic token refresh
  useEffect(() => {
    if (accessToken) {
      const tokenPayload = parseJwtPayload(accessToken);
      if (tokenPayload && tokenPayload.exp) {
        const expirationTime = tokenPayload.exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        const timeUntilExpiry = expirationTime - currentTime;

        // Refresh token 5 minutes before it expires
        const refreshTime = Math.max(timeUntilExpiry - 5 * 60 * 1000, 30000); // At least 30 seconds

        const refreshTimer = setTimeout(async () => {
          await refreshToken();
        }, refreshTime);

        return () => clearTimeout(refreshTimer);
      }
    }
  }, [accessToken]);

  const initializeAuth = async () => {
    try {
      setIsLoading(true);
      
      // Try to get current user info (this will work if we have a valid refresh token cookie)
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setUser(data.data);
          // Try to refresh access token
          await refreshToken();
        }
      }
    } catch (error) {
      console.log('No existing session found');
    } finally {
      setIsLoading(false);
    }
  };

  const parseJwtPayload = (token: string) => {
    try {
      const payload = token.split('.')[1];
      return JSON.parse(atob(payload));
    } catch (error) {
      return null;
    }
  };

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        credentials: 'include', // Include cookies for refresh token
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.data.user);
        setAccessToken(data.data.tokens.access_token);
        
        // Store access token in memory/localStorage for API requests
        localStorage.setItem('access_token', data.data.tokens.access_token);
        
        return true;
      } else {
        setError(data.detail?.message || data.message || 'Login failed');
        return false;
      }
    } catch (error) {
      setError('Network error. Please check your connection.');
      console.error('Login error:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        credentials: 'include', // Include cookies for refresh token
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const responseData = await response.json();

      if (response.ok && responseData.success) {
        setUser(responseData.data.user);
        setAccessToken(responseData.data.tokens.access_token);
        
        // Store access token in memory/localStorage for API requests
        localStorage.setItem('access_token', responseData.data.tokens.access_token);
        
        return true;
      } else {
        setError(responseData.detail?.message || responseData.message || 'Registration failed');
        return false;
      }
    } catch (error) {
      setError('Network error. Please check your connection.');
      console.error('Registration error:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout endpoint to invalidate refresh token
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API call success
      setUser(null);
      setAccessToken(null);
      localStorage.removeItem('access_token');
      setError(null);
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Include refresh token cookie
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setAccessToken(data.data.tokens.access_token);
        localStorage.setItem('access_token', data.data.tokens.access_token);
        return true;
      } else {
        // Refresh token is invalid or expired, log out user
        await logout();
        return false;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      await logout();
      return false;
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// HOC for protected routes
interface RequireAuthProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({ 
  children, 
  fallback = <div>Please log in to access this page.</div> 
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-primary">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// HTTP interceptor utility for adding auth headers
export const createAuthenticatedFetch = (originalFetch = fetch) => {
  return async (url: RequestInfo | URL, init: RequestInit = {}) => {
    // Get access token from localStorage
    const accessToken = localStorage.getItem('access_token');
    
    // Add authorization header if token exists
    if (accessToken) {
      init.headers = {
        ...init.headers,
        Authorization: `Bearer ${accessToken}`,
      };
    }

    // Always include credentials for refresh token cookie
    init.credentials = 'include';

    try {
      const response = await originalFetch(url, init);
      
      // If we get a 401, try to refresh the token once
      if (response.status === 401 && accessToken) {
        const refreshResponse = await originalFetch('/api/auth/refresh', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json();
          if (refreshData.success) {
            // Update stored token
            localStorage.setItem('access_token', refreshData.data.tokens.access_token);
            
            // Retry original request with new token
            init.headers = {
              ...init.headers,
              Authorization: `Bearer ${refreshData.data.tokens.access_token}`,
            };
            return originalFetch(url, init);
          }
        }
        
        // If refresh failed, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }

      return response;
    } catch (error) {
      throw error;
    }
  };
};

// Replace global fetch with authenticated version
if (typeof window !== 'undefined') {
  window.fetch = createAuthenticatedFetch(window.fetch);
}