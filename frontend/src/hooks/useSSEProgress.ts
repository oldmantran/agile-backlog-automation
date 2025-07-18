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

  const connect = useCallback((jobId: string) => {
    // Disconnect any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      console.log(`🔗 Connecting to SSE stream for job: ${jobId}`);
      
      // Create EventSource connection
      const eventSource = new EventSource(`http://localhost:8000/api/progress/stream/${jobId}`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log(`✅ SSE connection opened for job: ${jobId}`);
        setIsConnected(true);
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const data: ProgressUpdate = JSON.parse(event.data);
          console.log(`📡 SSE update for job ${jobId}:`, data);
          
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
          console.error('Failed to parse SSE message:', parseError);
          setError('Failed to parse server message');
        }
      };

      eventSource.onerror = (event) => {
        console.error(`❌ SSE connection error for job ${jobId}:`, event);
        setError('SSE connection failed');
        setIsConnected(false);
        
        // Close the connection
        eventSource.close();
        eventSourceRef.current = null;
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
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
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