import { useEffect, useRef, useState, useCallback } from 'react';

interface ProgressUpdate {
  type: 'connected' | 'progress' | 'final' | 'error';
  jobId: string;
  progress?: number;
  status?: string;
  currentAction?: string;
  message?: string;
  timestamp?: string;
}

interface UseSSEProgressReturn {
  isConnected: boolean;
  lastUpdate: ProgressUpdate | null;
  error: string | null;
  connect: (jobId: string) => void;
  disconnect: () => void;
}

export const useSSEProgress = (): UseSSEProgressReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<ProgressUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback((jobId: string) => {
    // Disconnect any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      console.log(`🔗 Connecting to SSE stream for job: ${jobId}`);
      
      // Create EventSource connection with proper error handling
      const eventSource = new EventSource(`http://localhost:8000/api/progress/stream/${jobId}`, {
        withCredentials: false // Important: disable credentials for CORS
      });
      eventSourceRef.current = eventSource;

      eventSource.onopen = (event) => {
        console.log(`✅ SSE connection opened for job: ${jobId}`, event);
        setIsConnected(true);
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          console.log(`📡 Raw SSE message: ${event.data}`);
          const data: ProgressUpdate = JSON.parse(event.data);
          console.log(`📊 Parsed SSE update for job ${jobId}:`, data);
          
          setLastUpdate(data);
          
          // Handle different message types
          switch (data.type) {
            case 'connected':
              console.log(`🔗 SSE connected for job: ${jobId}`);
              break;
            case 'progress':
              console.log(`📊 Progress update: ${data.progress}% - ${data.currentAction}`);
              break;
            case 'final':
              console.log(`🏁 Job completed: ${data.status}`);
              // Close connection when job is finished
              eventSource.close();
              setIsConnected(false);
              break;
            case 'error':
              console.error(`❌ SSE error: ${data.message}`);
              setError(data.message || 'Unknown error');
              break;
          }
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError, 'Raw data:', event.data);
          setError('Failed to parse server message');
        }
      };

      eventSource.onerror = (event) => {
        console.error(`❌ SSE connection error for job ${jobId}:`, event);
        
        // Check if the connection is actually closed
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log('SSE connection is closed');
          setError('SSE connection closed');
          setIsConnected(false);
        } else if (eventSource.readyState === EventSource.CONNECTING) {
          console.log('SSE connection is reconnecting...');
          setError('SSE connection lost, attempting to reconnect...');
          setIsConnected(false);
        } else {
          console.log('SSE connection error, but still open');
          setError('SSE connection error');
        }
      };

    } catch (err) {
      console.error(`❌ Failed to create SSE connection for job ${jobId}:`, err);
      setError('Failed to establish SSE connection');
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('🔌 Disconnecting SSE connection');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setError(null);
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    lastUpdate,
    error,
    connect,
    disconnect
  };
}; 