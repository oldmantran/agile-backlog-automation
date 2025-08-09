import { useEffect, useRef, useState, useCallback } from 'react';

interface ProgressUpdate {
  type: 'connected' | 'progress' | 'final' | 'error';
  jobId: string;
  progress?: number;
  status?: string;
  currentAction?: string;
  currentAgent?: string;
  message?: string;
  timestamp?: string;
  etag?: string;
  source?: 'memory' | 'database';
}

interface UseHybridProgressReturn {
  isConnected: boolean;
  lastUpdate: ProgressUpdate | null;
  error: string | null;
  connectionType: 'sse' | 'polling' | 'disconnected';
  connect: (jobId: string) => void;
  disconnect: () => void;
}

/**
 * Hybrid progress tracking hook with SSE primary + DB polling fallback.
 * 
 * Features:
 * - SSE for low-latency real-time updates (primary)
 * - Automatic fallback to polling on SSE disconnect/error
 * - Exponential backoff for polling retries
 * - ETags for conditional requests to minimize bandwidth
 * - Automatic reconnection attempts
 */
export const useHybridProgress = (): UseHybridProgressReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<ProgressUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionType, setConnectionType] = useState<'sse' | 'polling' | 'disconnected'>('disconnected');

  // Refs for cleanup and state management
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const lastEtagRef = useRef<string | null>(null);
  const pollingBackoffRef = useRef<number>(3000); // Start with 3 seconds
  const maxBackoffRef = useRef<number>(30000); // Max 30 seconds
  const failedAttemptsRef = useRef<number>(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setConnectionType('disconnected');
    setIsConnected(false);
  }, []);

  // Polling fallback function
  const startPolling = useCallback(async (jobId: string, immediate: boolean = false) => {
    if (!jobId) return;

    const poll = async () => {
      try {
        console.log(`🔄 Polling progress for job ${jobId} (backoff: ${pollingBackoffRef.current}ms)`);
        
        const headers: Record<string, string> = {};
        if (lastEtagRef.current) {
          headers['If-None-Match'] = lastEtagRef.current;
        }

        const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/progress`, {
          headers
        });

        if (response.status === 304) {
          // Not modified - no new data
          console.log(`📊 No progress change for job ${jobId}`);
          failedAttemptsRef.current = 0; // Reset backoff on successful request
          pollingBackoffRef.current = 3000; // Reset to minimum interval
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`📊 Polled progress for job ${jobId}:`, data);

        // Update state
        const progressUpdate: ProgressUpdate = {
          type: data.status === 'completed' ? 'final' : 'progress',
          jobId: data.jobId,
          progress: data.progress,
          status: data.status,
          currentAction: data.currentAction,
          currentAgent: data.currentAgent,
          timestamp: data.lastUpdated,
          etag: data.etag,
          source: data.source
        };

        setLastUpdate(progressUpdate);
        setError(null);
        lastEtagRef.current = data.etag;
        
        // Reset backoff on success
        failedAttemptsRef.current = 0;
        pollingBackoffRef.current = 3000;

        // Stop polling if job is complete
        if (data.status === 'completed' || data.status === 'failed') {
          console.log(`🏁 Job ${jobId} finished, stopping polling`);
          cleanup();
        }

      } catch (error) {
        failedAttemptsRef.current++;
        console.error(`❌ Polling error for job ${jobId} (attempt ${failedAttemptsRef.current}):`, error);
        
        setError(error instanceof Error ? error.message : 'Polling failed');
        
        // Exponential backoff with jitter
        pollingBackoffRef.current = Math.min(
          pollingBackoffRef.current * 1.5 + Math.random() * 1000,
          maxBackoffRef.current
        );

        // Stop polling after too many failures
        if (failedAttemptsRef.current >= 10) {
          console.error(`❌ Too many polling failures for job ${jobId}, giving up`);
          setError('Polling failed after multiple attempts');
          cleanup();
        }
      }
    };

    // Immediate poll if requested
    if (immediate) {
      await poll();
    }

    // Set up interval polling
    pollingIntervalRef.current = setInterval(poll, pollingBackoffRef.current);
    setConnectionType('polling');
    setIsConnected(true);
  }, [cleanup]);

  // SSE connection function
  const connectSSE = useCallback((jobId: string) => {
    try {
      console.log(`🔗 Attempting SSE connection for job: ${jobId}`);
      
      const eventSource = new EventSource(`http://localhost:8000/api/progress/stream/${jobId}`, {
        withCredentials: false
      });
      eventSourceRef.current = eventSource;

      eventSource.onopen = (event) => {
        console.log(`✅ SSE connection opened for job: ${jobId}`, event);
        setConnectionType('sse');
        setIsConnected(true);
        setError(null);
        failedAttemptsRef.current = 0; // Reset failure count
      };

      eventSource.onmessage = (event) => {
        try {
          console.log(`📡 SSE message for job ${jobId}:`, event.data);
          const data: ProgressUpdate = JSON.parse(event.data);
          
          setLastUpdate(data);
          lastEtagRef.current = data.etag || null;
          
          // Handle different message types
          switch (data.type) {
            case 'final':
              console.log(`🏁 Job ${jobId} completed via SSE`);
              // Keep connection for a bit then cleanup
              setTimeout(() => cleanup(), 2000);
              break;
            case 'error':
              console.error(`❌ SSE job error: ${data.message}`);
              setError(data.message || 'Job failed');
              break;
          }
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError, 'Raw data:', event.data);
          setError('Failed to parse server message');
        }
      };

      eventSource.onerror = (event) => {
        console.warn(`⚠️ SSE connection error for job ${jobId}:`, event);
        
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log(`🔄 SSE connection closed, falling back to polling for job ${jobId}`);
          eventSource.close();
          eventSourceRef.current = null;
          
          // Fallback to polling
          startPolling(jobId, true); // Immediate first poll
        } else {
          setError('SSE connection error, attempting reconnection...');
          
          // Attempt to reconnect SSE after a delay
          reconnectTimeoutRef.current = setTimeout(() => {
            if (currentJobIdRef.current === jobId) {
              console.log(`🔄 Attempting SSE reconnection for job ${jobId}`);
              connectSSE(jobId);
            }
          }, 5000);
        }
      };

    } catch (err) {
      console.error(`❌ Failed to create SSE connection for job ${jobId}:`, err);
      setError('Failed to establish SSE connection');
      
      // Fallback to polling immediately
      startPolling(jobId, true);
    }
  }, [startPolling, cleanup]);

  // Main connect function
  const connect = useCallback((jobId: string) => {
    cleanup(); // Clean up any existing connections
    
    currentJobIdRef.current = jobId;
    lastEtagRef.current = null;
    failedAttemptsRef.current = 0;
    pollingBackoffRef.current = 3000;
    
    setError(null);
    
    // Try SSE first
    connectSSE(jobId);
  }, [connectSSE, cleanup]);

  // Disconnect function
  const disconnect = useCallback(() => {
    currentJobIdRef.current = null;
    cleanup();
  }, [cleanup]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    isConnected,
    lastUpdate,
    error,
    connectionType,
    connect,
    disconnect
  };
};