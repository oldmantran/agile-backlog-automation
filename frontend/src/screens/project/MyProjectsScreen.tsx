import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { FiActivity, FiCheckCircle, FiXCircle, FiClock, FiTrash2, FiAlertTriangle, FiFolder, FiPlus, FiRotateCcw, FiCalendar, FiBarChart3 } from 'react-icons/fi';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { BacklogJob } from '../../types/backlogJob';
import { Project } from '../../types/project';
import { useSSEProgress } from '../../hooks/useSSEProgress';

interface JobInfo {
  jobId: string;
  projectName: string;
  startTime: string;
  status?: string;
  progress?: number;
  currentAction?: string;
  error?: string;
}

interface ComponentError {
  component: string;
  error: string;
  timestamp: string;
  details?: any;
}

const USER_EMAIL = 'kevin.tran@c4workx.com'; // TODO: Replace with dynamic user email if available

// Project History Card Component
interface ProjectHistoryCardProps {
  job: BacklogJob;
  onDelete: () => void;
  onRetry: () => void;
  isRetrying?: boolean;
}

const ProjectHistoryCard: React.FC<ProjectHistoryCardProps> = ({ job, onDelete, onRetry, isRetrying = false }) => {
  // Parse staging summary from raw_summary
  const getStagingSummary = () => {
    try {
      const rawSummary = job.raw_summary as any;
      return rawSummary?.staging_summary || {};
    } catch {
      return {};
    }
  };

  const getUploadMetrics = () => {
    const stagingSummary = getStagingSummary();
    const byStatus = stagingSummary.by_status || {};
    const totalGenerated = job.epics_generated + job.features_generated + job.user_stories_generated + 
                          job.tasks_generated + job.test_cases_generated;
    const totalUploaded = byStatus.success || 0;
    const totalFailed = byStatus.failed || 0;
    const failureRate = totalGenerated > 0 ? ((totalFailed + byStatus.skipped || 0) / totalGenerated) * 100 : 0;
    
    return {
      totalGenerated,
      totalUploaded,
      totalFailed,
      failureRate: Math.round(failureRate * 10) / 10,
      hasFailures: totalFailed > 0
    };
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  const metrics = getUploadMetrics();
  const { date, time } = formatDate(job.created_at);
  const stagingSummary = getStagingSummary();
  const jobId = (job.raw_summary as any)?.job_id || 'N/A';

  return (
    <Card className={`tron-card bg-card/50 backdrop-blur-sm hover:shadow-lg transition-all ${
      metrics.hasFailures 
        ? 'border-orange-500/50 shadow-orange-500/20 shadow-md' 
        : 'border-primary/30'
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-foreground glow-cyan text-lg">
              {job.project_name}
            </CardTitle>
            <div className="flex items-center space-x-2 mt-1 text-xs text-muted-foreground font-mono">
              <FiCalendar className="w-3 h-3" />
              <span>{date} at {time}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono mt-1">
              Job ID: {jobId.length > 20 ? `${jobId.substring(0, 20)}...` : jobId}
            </p>
          </div>
          <Badge 
            variant={job.status === 'completed' ? 'default' : job.status === 'failed' ? 'destructive' : 'secondary'}
            className="font-mono text-xs"
          >
            {job.status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Generation Summary */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm font-medium">
            <FiBarChart3 className="w-4 h-4 text-primary" />
            <span>Generation Summary</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Items:</span>
              <span className="font-mono">{metrics.totalGenerated}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Duration:</span>
              <span className="font-mono">{formatDuration(job.execution_time_seconds || 0)}</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center">
              <div className="text-muted-foreground">Epics</div>
              <div className="font-mono font-semibold">{job.epics_generated}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Features</div>
              <div className="font-mono font-semibold">{job.features_generated}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Stories</div>
              <div className="font-mono font-semibold">{job.user_stories_generated}</div>
            </div>
          </div>
        </div>

        {/* Upload Results */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Upload Results</span>
            {metrics.hasFailures && (
              <Badge variant="destructive" className="text-xs animate-pulse">
                {metrics.failureRate}% Failed
              </Badge>
            )}
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Uploaded:</span>
              <span className="font-mono">{metrics.totalUploaded}/{metrics.totalGenerated}</span>
            </div>
            <Progress 
              value={metrics.totalGenerated > 0 ? (metrics.totalUploaded / metrics.totalGenerated) * 100 : 0} 
              className="h-2"
            />
            {metrics.totalFailed > 0 && (
              <div className="text-xs text-orange-600 bg-orange-50 dark:bg-orange-950 px-2 py-1 rounded">
                ⚠️ {metrics.totalFailed} items failed to upload - click retry button below
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center pt-2 border-t border-border">
          <div className="flex space-x-2">
            {metrics.hasFailures && (
              <Button
                size="sm"
                variant={isRetrying ? "outline" : "default"}
                onClick={onRetry}
                disabled={isRetrying}
                className={`text-xs ${!isRetrying ? 'bg-orange-500 hover:bg-orange-600 text-white' : ''}`}
              >
                {isRetrying ? (
                  <FiActivity className="w-3 h-3 mr-1 animate-spin" />
                ) : (
                  <FiRotateCcw className="w-3 h-3 mr-1" />
                )}
                {isRetrying ? 'Retrying...' : 'Retry Failed Uploads'}
              </Button>
            )}
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={onDelete}
            className="text-red-400 hover:text-red-300 text-xs"
          >
            <FiTrash2 className="w-3 h-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Error Boundary Component for Progress Bar
class ProgressBarErrorBoundary extends React.Component<
  { job: JobInfo; children: React.ReactNode },
  { hasError: boolean; error: string }
> {
  constructor(props: { job: JobInfo; children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Progress Bar Error for job ${this.props.job.jobId}:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-red-500 bg-red-50 dark:bg-red-950 rounded-md">
          <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
            <FiAlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">Progress Bar Error</span>
          </div>
          <p className="text-xs text-red-500 dark:text-red-400 mt-1">
            Job: {this.props.job.jobId} | Error: {this.state.error}
          </p>
          <Button 
            size="sm" 
            variant="outline" 
            className="mt-2 text-xs"
            onClick={() => this.setState({ hasError: false, error: '' })}
          >
            Retry
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

const MyProjectsScreen: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState<JobInfo[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [backlogJobs, setBacklogJobs] = useState<BacklogJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<ComponentError[]>([]);
  const [debugMode, setDebugMode] = useState(false);
  const [retryingJobs, setRetryingJobs] = useState<Set<number>>(new Set());
  const hasMounted = useRef(false);
  
  // SSE progress hook for real-time updates
  const { isConnected: sseConnected, lastUpdate: sseUpdate, error: sseError, connect: connectSSE, disconnect: disconnectSSE } = useSSEProgress();

  // Enhanced error logging
  const logError = (component: string, error: any, details?: any) => {
    const errorInfo: ComponentError = {
      component,
      error: error?.message || error?.toString() || 'Unknown error',
      timestamp: new Date().toISOString(),
      details
    };
    
    console.error(`[${component}] Error:`, errorInfo);
    setErrors(prev => [...prev, errorInfo]);
    
    // Log to localStorage for debugging
    const debugLogs = JSON.parse(localStorage.getItem('debugLogs') || '[]');
    debugLogs.push(errorInfo);
    localStorage.setItem('debugLogs', JSON.stringify(debugLogs.slice(-50))); // Keep last 50 errors
  };

  const loadActiveJobs = useCallback(() => {
    try {
      console.log('Loading active jobs from localStorage...');
      const stored = localStorage.getItem('activeJobs');
      if (stored) {
        const jobs = JSON.parse(stored);
        console.log('Loaded active jobs:', jobs);
        
        // Filter out old completed/failed jobs (older than 10 minutes)
        const now = Date.now();
        const filteredJobs = jobs.filter((job: JobInfo) => {
          const jobAge = now - new Date(job.startTime).getTime();
          if (job.status === 'completed' || job.status === 'failed') {
            return jobAge < 600000; // Keep for 10 minutes
          }
          return true; // Keep all running/queued jobs
        });
        
        console.log('Filtered active jobs:', filteredJobs);
        setActiveJobs(filteredJobs);
        
        // Update localStorage with filtered jobs
        localStorage.setItem('activeJobs', JSON.stringify(filteredJobs));
        
        // Log cleanup if we removed old jobs
        if (filteredJobs.length !== jobs.length) {
          console.log(`Cleaned up ${jobs.length - filteredJobs.length} old jobs from localStorage`);
        }
      } else {
        console.log('No active jobs found in localStorage');
        setActiveJobs([]);
      }
    } catch (error) {
      logError('loadActiveJobs', error, 'localStorage parsing error');
      setActiveJobs([]);
    }
  }, []);

  // Function to clear all stale jobs
  const clearStaleJobs = useCallback(() => {
    try {
      console.log('🧹 Clearing all stale jobs from localStorage...');
      localStorage.removeItem('activeJobs');
      setActiveJobs([]);
      console.log('✅ All stale jobs cleared');
    } catch (error) {
      logError('clearStaleJobs', error, 'Failed to clear stale jobs');
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      console.log('Loading projects from API...');
      const response = await projectApi.listProjects(1, 20);
      console.log('Projects API response:', response);
      
      // Simple, robust handling - just check if response exists and has projects
      if (response && response.projects) {
        setProjects(response.projects);
      } else {
        console.warn('No projects found in API response:', response);
        setProjects([]);
      }
    } catch (error) {
      logError('loadProjects', error, 'API call failed');
      setProjects([]);
      // Retry after 5 seconds if it's a network error
      if (error instanceof Error && error.message.includes('Network error')) {
        setTimeout(() => {
          console.log('Retrying loadProjects...');
          loadProjects();
        }, 5000);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBacklogJobs = useCallback(async () => {
    try {
      console.log('Loading backlog jobs from API...');
      const jobs = await backlogApi.getBacklogJobs(USER_EMAIL, true, true, true);
      console.log('Backlog jobs API response:', jobs);
      setBacklogJobs(jobs);
    } catch (error) {
      logError('loadBacklogJobs', error, 'API call failed');
      setBacklogJobs([]);
      // Retry after 5 seconds if it's a network error
      if (error instanceof Error && error.message.includes('Network error')) {
        setTimeout(() => {
          console.log('Retrying loadBacklogJobs...');
          loadBacklogJobs();
        }, 5000);
      }
    }
  }, []);

  const handleDeleteBacklogJob = useCallback(async (jobId: number) => {
    try {
      console.log(`Deleting backlog job ${jobId}...`);
      await backlogApi.deleteBacklogJob(jobId);
      setBacklogJobs(prev => prev.filter(job => job.id !== jobId));
      console.log(`Backlog job ${jobId} deleted successfully`);
    } catch (error) {
      logError('handleDeleteBacklogJob', error, { jobId });
    }
  }, []);

  const handleRetryFailedUploads = useCallback(async (job: BacklogJob) => {
    try {
      const jobId = job.id;
      setRetryingJobs(prev => new Set([...prev, jobId]));
      
      console.log(`Retrying failed uploads for job ${jobId}...`);
      
      // Get job ID from raw_summary to call retry API
      const rawSummary = job.raw_summary as any;
      const stagingJobId = rawSummary?.job_id || `job_${job.created_at.replace(/[^0-9]/g, '')}`;
      
      // Call the retry API
      const response = await fetch('/api/retry-failed-uploads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: stagingJobId,
          action: 'retry'
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log(`Retry result for job ${jobId}:`, result);
      
      // Refresh the backlog jobs to get updated status
      await loadBacklogJobs();
      
    } catch (error) {
      logError('handleRetryFailedUploads', error, { jobId: job.id });
    } finally {
      setRetryingJobs(prev => {
        const updated = new Set(prev);
        updated.delete(job.id);
        return updated;
      });
    }
  }, [loadBacklogJobs]);

  // SSE-based job updates
  const updateJobsFromSSE = useCallback(() => {
    try {
      if (!sseUpdate) return;
      
      const stored = localStorage.getItem('activeJobs');
      if (!stored) {
        return;
      }

      const jobs: JobInfo[] = JSON.parse(stored);
      const updatedJobs: JobInfo[] = [];

      for (const job of jobs) {
        // Check if this SSE update is for our job
        if (sseUpdate.jobId === job.jobId) {
          const updatedJob = {
            ...job,
            status: sseUpdate.status || job.status,
            progress: sseUpdate.progress || job.progress || 0,
            currentAction: sseUpdate.currentAction || job.currentAction || 'Working...',
            error: sseUpdate.message || job.error
          };
          
          // Only log progress changes
          if (sseUpdate.progress !== job.progress) {
            console.log(`📡 Job ${job.jobId} progress: ${job.progress}% → ${sseUpdate.progress}%`);
          }

          if (updatedJob.status === 'running' || updatedJob.status === 'queued') {
            updatedJobs.push(updatedJob);
          } else if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            const jobAge = Date.now() - new Date(job.startTime).getTime();
            if (jobAge < 600000) {
              updatedJobs.push(updatedJob);
            }
          }
        } else {
          // Keep existing job if SSE update is for different job
          updatedJobs.push(job);
        }
      }

      setActiveJobs(prev => updatedJobs);
      localStorage.setItem('activeJobs', JSON.stringify(updatedJobs));
    } catch (error) {
      logError('updateJobsFromSSE', error, 'SSE update error');
    }
  }, [sseUpdate]);

  const removeJob = useCallback((jobId: string) => {
    try {
      setActiveJobs(prev => {
        const updated = prev.filter(job => job.jobId !== jobId);
        localStorage.setItem('activeJobs', JSON.stringify(updated));
        return updated;
      });
      console.log(`Removed job ${jobId} from active jobs`);
    } catch (error) {
      logError('removeJob', error, { jobId });
    }
  }, []);

  const getJobStatusIcon = useCallback((status?: string) => {
    try {
      switch (status) {
        case 'completed': return <FiCheckCircle className="w-5 h-5 text-green-400" />;
        case 'failed': return <FiXCircle className="w-5 h-5 text-red-400" />;
        case 'running': return <FiActivity className="w-5 h-5 text-blue-400 animate-pulse" />;
        case 'queued': return <FiClock className="w-5 h-5 text-yellow-400" />;
        default: return <FiActivity className="w-5 h-5 text-gray-400" />;
      }
    } catch (error) {
      logError('getJobStatusIcon', error, { status });
      return <FiActivity className="w-5 h-5 text-gray-400" />;
    }
  }, []);

  const getJobStatusColor = useCallback((status?: string) => {
    try {
      switch (status) {
        case 'completed': return 'text-green-400 border-green-400';
        case 'failed': return 'text-red-400 border-red-400';
        case 'running': return 'text-blue-400 border-blue-400';
        case 'queued': return 'text-yellow-400 border-yellow-400';
        default: return 'text-gray-400 border-gray-400';
      }
    } catch (error) {
      logError('getJobStatusColor', error, { status });
      return 'text-gray-400 border-gray-400';
    }
  }, []);

  // Debug panel component
  const DebugPanel = () => {
    if (!debugMode) return null;
    
    return (
      <Card className="mb-6 border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
        <CardHeader>
          <CardTitle className="text-yellow-700 dark:text-yellow-300">Debug Panel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-yellow-700 dark:text-yellow-300">Active Jobs:</h4>
              <pre className="text-xs bg-yellow-100 dark:bg-yellow-900 p-2 rounded overflow-auto">
                {JSON.stringify(activeJobs, null, 2)}
              </pre>
            </div>
            <div>
              <h4 className="font-semibold text-yellow-700 dark:text-yellow-300">Errors:</h4>
              <pre className="text-xs bg-yellow-100 dark:bg-yellow-900 p-2 rounded overflow-auto">
                {JSON.stringify(errors, null, 2)}
              </pre>
            </div>
            <div className="flex space-x-2">
              <Button 
                size="sm" 
                onClick={() => {
                  localStorage.removeItem('debugLogs');
                  setErrors([]);
                }}
              >
                Clear Debug Logs
              </Button>
              <Button 
                size="sm" 
                variant="destructive"
                onClick={clearStaleJobs}
              >
                Clear Stale Jobs
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  useEffect(() => {
    // Prevent multiple initializations in React 18 Strict Mode
    if (hasMounted.current) {
      return;
    }
    hasMounted.current = true;
    
    console.log('MyProjectsScreen: Component mounting...');
    try {
      loadActiveJobs();
      
      // Stagger API calls to prevent overwhelming the backend
      setTimeout(() => {
        loadProjects();
      }, 500);
      
      setTimeout(() => {
        loadBacklogJobs();
      }, 1000);
      
    } catch (error) {
      logError('MyProjectsScreen', error, 'Component mount error');
    }
  }, [loadActiveJobs, loadProjects, loadBacklogJobs]);

  // Set up SSE connections for active jobs
  useEffect(() => {
    if (activeJobs.length > 0) {
      console.log('🔗 Setting up SSE connections for active jobs:', activeJobs.map(job => job.jobId));
      
      // Connect to SSE for the first active job (we'll handle multiple jobs later)
      const firstJob = activeJobs[0];
      connectSSE(firstJob.jobId);
      
      return () => {
        console.log('🔌 Disconnecting SSE');
        disconnectSSE();
      };
    }
  }, [activeJobs, connectSSE, disconnectSSE]);

  // Effect to handle SSE updates
  useEffect(() => {
    if (sseUpdate) {
      updateJobsFromSSE();
    }
  }, [sseUpdate, updateJobsFromSSE]);

  return (
    <div className="min-h-screen">
      {/* Header and Sidebar */}
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Main Content */}
      <div className="ml-0 lg:ml-[250px] pt-[70px] transition-all duration-300 ease-in-out">
        <div className="min-h-screen bg-background tron-grid relative overflow-hidden">
          {/* Enhanced grid background overlay */}
          <div className="absolute inset-0 opacity-20">
            <div className="grid-pattern absolute inset-0"></div>
          </div>

          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-15">
            <div className="scan-line absolute w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent"></div>
          </div>

          <div className="relative z-10 container mx-auto px-6 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-4xl font-bold text-foreground tracking-wider glow-cyan mb-2">
                    MY PROJECTS
                  </h1>
                  <p className="text-muted-foreground font-mono">
                    MONITOR BACKLOG GENERATION PROGRESS
                  </p>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setDebugMode(!debugMode)}
                    className="text-xs"
                  >
                    {debugMode ? 'Hide Debug' : 'Show Debug'}
                  </Button>
                  <Button
                    onClick={() => navigate('/simple-project-wizard')}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    <FiFolder className="w-4 h-4 mr-2" />
                    Create New Project
                  </Button>
                </div>
              </div>
            </div>

            {/* Debug Panel */}
            <DebugPanel />

            {/* SSE Error Display */}
            {sseError && (
              <Alert className="mb-6 border-red-500 bg-red-50 dark:bg-red-950">
                <FiXCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                <AlertDescription className="text-red-700 dark:text-red-300">
                  <strong>SSE Connection Error:</strong> {sseError}
                </AlertDescription>
              </Alert>
            )}

            {/* Error Display */}
            {errors.length > 0 && (
              <Alert className="mb-6 border-red-500 bg-red-50 dark:bg-red-950">
                <FiAlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                <AlertDescription>
                  <div className="text-red-700 dark:text-red-300">
                    <strong>Component Errors Detected:</strong>
                    <ul className="mt-2 space-y-1">
                      {errors.slice(-3).map((error, index) => (
                        <li key={index} className="text-xs">
                          <strong>{error.component}:</strong> {error.error}
                        </li>
                      ))}
                    </ul>
                    {errors.length > 3 && (
                      <p className="text-xs mt-1">
                        ... and {errors.length - 3} more errors. Check console for details.
                      </p>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Active Jobs Section */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                ACTIVE BACKLOG GENERATION
              </h2>
              {activeJobs.length > 0 ? (
                <div className="space-y-6">
                  {activeJobs.map((job) => (
                    <Card key={job.jobId} className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            {getJobStatusIcon(job.status)}
                            <div>
                              <CardTitle className="text-foreground glow-cyan">
                                {job.projectName}
                              </CardTitle>
                              <p className="text-sm text-muted-foreground font-mono">
                                Job ID: {job.jobId}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant="outline" 
                              className={`font-mono ${getJobStatusColor(job.status)}`}
                            >
                              {job.status?.toUpperCase() || 'UNKNOWN'}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeJob(job.jobId)}
                              className="text-red-400 hover:text-red-300"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Progress Bar with Error Boundary */}
                        <ProgressBarErrorBoundary job={job}>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Progress</span>
                              <span className="text-foreground font-mono">{job.progress || 0}%</span>
                            </div>
                            { (job.progress === 0 && (job.status === 'queued' || job.status === 'running')) ? (
                              <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
                            ) : (
                              <Progress 
                                value={job.progress || 0} 
                                className="h-2"
                              />
                            ) }
                            <p className="text-sm text-muted-foreground font-mono">
                              {job.currentAction || 'Initializing...'}
                            </p>
                          </div>
                        </ProgressBarErrorBoundary>

                        {/* Error Display for Job */}
                        {job.error && (
                          <Alert className="border-red-500 bg-red-50 dark:bg-red-950">
                            <FiXCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                            <AlertDescription className="text-red-700 dark:text-red-300">
                              <strong>Job Error:</strong> {job.error}
                            </AlertDescription>
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                  <CardContent className="pt-6 text-center">
                    <FiActivity className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-foreground mb-2">No Active Backlog Generation</h3>
                    <p className="text-muted-foreground mb-4">
                      Start a new backlog generation to see progress here.
                    </p>
                    <Button
                      onClick={() => navigate('/simple-project-wizard')}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground"
                    >
                      <FiFolder className="w-4 h-4 mr-2" />
                      Generate New Backlog
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Projects Section */}
            {projects.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                  YOUR PROJECTS
                </h2>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {projects.map((project) => (
                    <Card key={project.id} className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <CardTitle className="text-foreground glow-cyan">
                          {project.basics?.name || 'Untitled Project'}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          {project.basics?.description || 'No description'}
                        </p>
                      </CardHeader>
                      <CardContent>
                        <div className="flex justify-between items-center">
                          <Badge variant="outline" className="font-mono">
                            {project.basics?.domain || 'General'}
                          </Badge>
                          <Button
                            size="sm"
                            onClick={() => navigate(`/project/${project.id}`)}
                            className="bg-primary hover:bg-primary/90 text-primary-foreground"
                          >
                            View Details
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Project History Section */}
            {backlogJobs.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                  PROJECT HISTORY
                </h2>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {backlogJobs.map((job) => (
                    <ProjectHistoryCard 
                      key={job.id} 
                      job={job} 
                      onDelete={() => handleDeleteBacklogJob(job.id)}
                      onRetry={() => handleRetryFailedUploads(job)}
                      isRetrying={retryingJobs.has(job.id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 dark:text-gray-400 mt-2">Loading projects...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyProjectsScreen;
