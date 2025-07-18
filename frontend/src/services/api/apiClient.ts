import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, ErrorResponse } from '../../types/api';

// API Client Configuration
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

// Custom error types
export class ApiError extends Error {
  public status: number;
  public code: string;
  public details?: any;

  constructor(message: string, status: number, code: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

// Response interceptor to standardize API responses
const responseInterceptor = (response: AxiosResponse) => {
  // Handle successful responses
  if (response.data && typeof response.data === 'object') {
    // Standardize response format
    if (response.data.data !== undefined) {
      // Unwrap the nested response structure
      return {
        ...response,
        data: response.data.data
      };
    } else {
      // Wrap non-standard responses
      return {
        ...response,
        data: response.data,
        success: true,
        message: 'Success'
      };
    }
  }
  return response;
};

// Error interceptor to standardize error handling
const errorInterceptor = (error: AxiosError): Promise<never> => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as any;
    
    let message = 'An error occurred';
    let code = 'UNKNOWN_ERROR';
    
    if (data) {
      message = data.message || data.error || message;
      code = data.code || code;
    }
    
    // Map HTTP status codes to user-friendly messages
    switch (status) {
      case 400:
        message = message || 'Invalid request data';
        code = 'BAD_REQUEST';
        break;
      case 401:
        message = 'Authentication required';
        code = 'UNAUTHORIZED';
        break;
      case 403:
        message = 'Access denied';
        code = 'FORBIDDEN';
        break;
      case 404:
        message = 'Resource not found';
        code = 'NOT_FOUND';
        break;
      case 422:
        message = message || 'Validation failed';
        code = 'VALIDATION_ERROR';
        break;
      case 429:
        message = 'Too many requests. Please try again later.';
        code = 'RATE_LIMITED';
        break;
      case 500:
        message = 'Server error. Please try again later.';
        code = 'SERVER_ERROR';
        break;
      case 502:
      case 503:
      case 504:
        message = 'Service temporarily unavailable. Please try again later.';
        code = 'SERVICE_UNAVAILABLE';
        break;
    }
    
    throw new ApiError(message, status, code, data);
  } else if (error.request) {
    // Network error (no response received)
    throw new NetworkError('Unable to connect to server. Please check your internet connection.');
  } else {
    // Other error
    throw new Error('An unexpected error occurred');
  }
};

// Retry logic for failed requests
const retryRequest = async (
  axiosInstance: AxiosInstance,
  config: any,
  retryCount: number = 0
): Promise<AxiosResponse> => {
  try {
    return await axiosInstance.request(config);
  } catch (error) {
    if (retryCount >= API_CONFIG.retryAttempts) {
      throw error;
    }
    
    // Only retry on network errors or 5xx server errors
    if (error instanceof NetworkError || 
        (error instanceof ApiError && error.status >= 500)) {
      
      // Exponential backoff
      const delay = API_CONFIG.retryDelay * Math.pow(2, retryCount);
      await new Promise(resolve => setTimeout(resolve, delay));
      
      return retryRequest(axiosInstance, config, retryCount + 1);
    }
    
    throw error;
  }
};

// Create axios instance with interceptors
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_CONFIG.baseURL,
    timeout: API_CONFIG.timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add response interceptor
  client.interceptors.response.use(responseInterceptor, errorInterceptor);

  return client;
};

// Main API client instance
const apiClient = createApiClient();

// Generic API methods with proper typing and error handling
export const apiClientMethods = {
  async get<T>(url: string, config?: any): Promise<T> {
    try {
      const response = await apiClient.get(url, config);
      return response.data as T;
    } catch (error) {
      throw error;
    }
  },

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response = await apiClient.post(url, data, config);
      return response.data as T;
    } catch (error) {
      throw error;
    }
  },

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response = await apiClient.put(url, data, config);
      return response.data as T;
    } catch (error) {
      throw error;
    }
  },

  async delete<T>(url: string, config?: any): Promise<T> {
    try {
      const response = await apiClient.delete(url, config);
      return response.data as T;
    } catch (error) {
      throw error;
    }
  },

  async patch<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response = await apiClient.patch(url, data, config);
      return response.data as T;
    } catch (error) {
      throw error;
    }
  }
};

// Health check method
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    await apiClient.get('/health');
    return true;
  } catch (error) {
    return false;
  }
};

// Connection status monitoring
export const monitorConnection = (onStatusChange: (connected: boolean) => void) => {
  let isConnected = true;
  
  const checkConnection = async () => {
    const connected = await checkApiHealth();
    if (connected !== isConnected) {
      isConnected = connected;
      onStatusChange(connected);
    }
  };
  
  // Check every 30 seconds
  const interval = setInterval(checkConnection, 30000);
  
  // Return cleanup function
  return () => clearInterval(interval);
};

export default apiClient; 