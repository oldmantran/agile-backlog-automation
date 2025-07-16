import { useState, useCallback } from 'react';
import { ApiError, NetworkError } from '../services/api/apiClient';

export interface ErrorState {
  hasError: boolean;
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

export interface UseApiErrorReturn {
  error: ErrorState;
  setError: (error: Error | string) => void;
  clearError: () => void;
  handleApiError: (error: unknown) => void;
  isNetworkError: boolean;
  isAuthError: boolean;
  isServerError: boolean;
  isClientError: boolean;
}

export const useApiError = (): UseApiErrorReturn => {
  const [error, setErrorState] = useState<ErrorState>({
    hasError: false,
    message: '',
  });

  const setError = useCallback((error: Error | string) => {
    if (typeof error === 'string') {
      setErrorState({
        hasError: true,
        message: error,
      });
    } else if (error instanceof ApiError) {
      setErrorState({
        hasError: true,
        message: error.message,
        code: error.code,
        status: error.status,
        details: error.details,
      });
    } else if (error instanceof NetworkError) {
      setErrorState({
        hasError: true,
        message: error.message,
        code: 'NETWORK_ERROR',
      });
    } else {
      setErrorState({
        hasError: true,
        message: error.message || 'An unexpected error occurred',
      });
    }
  }, []);

  const clearError = useCallback(() => {
    setErrorState({
      hasError: false,
      message: '',
    });
  }, []);

  const handleApiError = useCallback((error: unknown) => {
    if (error instanceof ApiError || error instanceof NetworkError || error instanceof Error) {
      setError(error);
    } else {
      setError('An unexpected error occurred');
    }
  }, [setError]);

  const isNetworkError = error.code === 'NETWORK_ERROR';
  const isAuthError = Boolean(error.status === 401 || error.status === 403);
  const isServerError = Boolean(error.status && error.status >= 500);
  const isClientError = Boolean(error.status && error.status >= 400 && error.status < 500);

  return {
    error,
    setError,
    clearError,
    handleApiError,
    isNetworkError,
    isAuthError,
    isServerError,
    isClientError,
  };
};

// Hook for handling async operations with error handling
export const useAsyncOperation = <T, Args extends any[]>(
  operation: (...args: Args) => Promise<T>
) => {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const { error, setError, clearError, handleApiError } = useApiError();

  const execute = useCallback(async (...args: Args): Promise<T | null> => {
    try {
      setIsLoading(true);
      clearError();
      
      const result = await operation(...args);
      setData(result);
      return result;
    } catch (err) {
      handleApiError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [operation, clearError, handleApiError]);

  return {
    execute,
    isLoading,
    data,
    error,
    clearError,
  };
};

// Hook for handling API calls with retry logic
export const useApiCall = <T, Args extends any[]>(
  apiCall: (...args: Args) => Promise<T>,
  retryCount: number = 3
) => {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const { error, setError, clearError, handleApiError } = useApiError();

  const execute = useCallback(async (...args: Args): Promise<T | null> => {
    let lastError: unknown;
    
    for (let attempt = 0; attempt <= retryCount; attempt++) {
      try {
        setIsLoading(true);
        setRetryAttempt(attempt);
        clearError();
        
        const result = await apiCall(...args);
        setData(result);
        return result;
      } catch (err) {
        lastError = err;
        
        // Don't retry on client errors (4xx)
        if (err instanceof ApiError && err.status >= 400 && err.status < 500) {
          break;
        }
        
        // Don't retry on auth errors
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          break;
        }
        
        // Wait before retry (exponential backoff)
        if (attempt < retryCount) {
          const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s, etc.
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      } finally {
        setIsLoading(false);
      }
    }
    
    // All retries failed
    handleApiError(lastError!);
    return null;
  }, [apiCall, retryCount, clearError, handleApiError]);

  return {
    execute,
    isLoading,
    data,
    error,
    retryAttempt,
    clearError,
  };
}; 