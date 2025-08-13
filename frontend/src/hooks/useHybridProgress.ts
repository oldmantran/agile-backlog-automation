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
  activeJobs: string[];
  connect: (jobId: string) => void;
  disconnect: (jobId?: string) => void; // Optional jobId to disconnect specific job
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
  const [activeJobs, setActiveJobs] = useState<string[]>([]);

  // Refs for cleanup and state management (single job for now, with multi-job infrastructure)
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const lastEtagRef = useRef<string | null>(null);
  const pollingBackoffRef = useRef<number>(3000); // Start with 3 seconds
  const maxBackoffRef = useRef<number>(30000); // Max 30 seconds
  const failedAttemptsRef = useRef<number>(0);
  
  // Multi-job infrastructure (for future use)
  const multiJobDataRef = useRef<Map<string, {
    eventSource?: EventSource;
    pollingInterval?: NodeJS.Timeout;
    reconnectTimeout?: NodeJS.Timeout;
    etag?: string;
    backoff: number;
    failedAttempts: number;
  }>>(new Map());

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

        const response = await fetch(`/api/jobs/${jobId}/progress`, {
          headers
        });

        if (response.status === 304) {
          // Not modified - no new data
          console.log(`📊 No progress change for job ${jobId}`);
          failedAttemptsRef.current = 0; // Reset backoff on successful request
          pollingBackoffRef.current = 3000; // Reset to minimum interval
          return;
        }

        // Explicitly handle job not found to avoid orphaned progress states
        if (response.status === 404) {
          setError('HTTP 404: Not Found');
          // Stop polling immediately; consumer can clear stale jobs
          cleanup();
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
          return;
        }
        
        // Restart polling with new backoff interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = setInterval(poll, pollingBackoffRef.current);
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
      
      const eventSource = new EventSource(`/api/progress/stream/${jobId}`, {
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
    // Update active jobs list
    setActiveJobs(prev => prev.includes(jobId) ? prev : [...prev, jobId]);
    
    // For single-job mode, clean up existing connection
    cleanup();
    
    currentJobIdRef.current = jobId;
    lastEtagRef.current = null;
    failedAttemptsRef.current = 0;
    pollingBackoffRef.current = 3000;
    
    // Initialize multi-job data structure
    multiJobDataRef.current.set(jobId, {
      backoff: 3000,
      failedAttempts: 0
    });
    
    setError(null);
    
    // Try SSE first
    connectSSE(jobId);
  }, [connectSSE, cleanup]);

  // Disconnect function (supports optional specific job)
  const disconnect = useCallback((jobId?: string) => {
    if (jobId) {
      // Disconnect specific job (future multi-job support)
      setActiveJobs(prev => prev.filter(id => id !== jobId));
      multiJobDataRef.current.delete(jobId);
      
      // If disconnecting current job, clean up
      if (currentJobIdRef.current === jobId) {
        currentJobIdRef.current = null;
        cleanup();
      }
    } else {
      // Disconnect all jobs
      setActiveJobs([]);
      multiJobDataRef.current.clear();
      currentJobIdRef.current = null;
      cleanup();
    }
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
    activeJobs,
    connect,
    disconnect
  };
};