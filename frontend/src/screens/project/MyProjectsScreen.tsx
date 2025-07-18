import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { FiActivity, FiCheckCircle, FiXCircle, FiClock, FiTrash2, FiAlertTriangle, FiFolder, FiPlus } from 'react-icons/fi';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { BacklogJob } from '../../types/backlogJob';
import { Project } from '../../types/project';

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

// Error Boundary Component for Progress Bar
const ProgressBarErrorBoundary: React.FC<{ job: JobInfo; children: React.ReactNode }> = ({ job, children }) => {
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<string>('');

  if (hasError) {
    console.error(`Progress Bar Error for job ${job.jobId}:`, error);
    return (
      <div className="p-4 border border-red-500 bg-red-50 dark:bg-red-950 rounded-md">
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <FiAlertTriangle className="w-4 h-4" />
          <span className="text-sm font-medium">Progress Bar Error</span>
        </div>
        <p className="text-xs text-red-500 dark:text-red-400 mt-1">
          Job: {job.jobId} | Error: {error}
        </p>
        <Button 
          size="sm" 
          variant="outline" 
          className="mt-2 text-xs"
          onClick={() => setHasError(false)}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div onError={(e) => {
      setHasError(true);
      setError(e.toString());
      console.error('Progress Bar rendering error:', e);
    }}>
      {children}
    </div>
  );
};

const MyProjectsScreen: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState<JobInfo[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [backlogJobs, setBacklogJobs] = useState<BacklogJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<ComponentError[]>([]);
  const [debugMode, setDebugMode] = useState(false);
  const hasMounted = useRef(false);

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

  const pollJobUpdates = useCallback(async () => {
    try {
      console.log('🔄 Starting pollJobUpdates...');
      const stored = localStorage.getItem('activeJobs');
      if (!stored) {
        console.log('No active jobs in localStorage');
        return;
      }

      const jobs: JobInfo[] = JSON.parse(stored);
      console.log(`Found ${jobs.length} active jobs to poll`);
      const updatedJobs: JobInfo[] = [];

      for (const job of jobs) {
        try {
          console.log(`Polling status for job: ${job.jobId}`);
          const status = await backlogApi.getGenerationStatus(job.jobId);
          console.log(`Job ${job.jobId} status:`, status);
          console.log(`Job ${job.jobId} progress from API:`, status.progress);
          
          const updatedJob = {
            ...job,
            status: status.status,
            progress: status.progress || 0,
            currentAction: status.currentAction || `${status.currentAgent} working...`,
            error: status.error
          };
          
          console.log(`Job ${job.jobId} updated:`, {
            oldProgress: job.progress,
            newProgress: status.progress,
            status: status.status,
            currentAction: status.currentAction
          });

          if (status.status === 'running' || status.status === 'queued') {
            updatedJobs.push(updatedJob);
          } else if (status.status === 'completed' || status.status === 'failed') {
            const jobAge = Date.now() - new Date(job.startTime).getTime();
            if (jobAge < 600000) {
              updatedJobs.push(updatedJob);
            }
          }
          
          // Small delay between job status checks to reduce backend load
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (error) {
          logError('pollJobUpdates', error, { jobId: job.jobId });
          
          // If it's a 404 error, the job no longer exists in the backend, so remove it
          if (error instanceof Error && error.message.includes('Resource not found')) {
            console.log(`Job ${job.jobId} not found in backend (404), removing from active jobs`);
            continue; // Skip adding this job to updatedJobs
          }
          
          // For other errors, keep the job if it's recent
          const jobAge = Date.now() - new Date(job.startTime).getTime();
          if (jobAge < 600000) {
            updatedJobs.push(job);
          }
        }
      }

      console.log('Updated jobs:', updatedJobs);
      setActiveJobs(prev => {
        console.log('Previous active jobs:', prev);
        return updatedJobs;
      });
      localStorage.setItem('activeJobs', JSON.stringify(updatedJobs));
    } catch (error) {
      logError('pollJobUpdates', error, 'Main polling error');
    }
  }, []);

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
        case 'completed': return 'text-green-400 border-green-400/50 bg-green-400/10';
        case 'failed': return 'text-red-400 border-red-400/50 bg-red-400/10';
        case 'running': return 'text-blue-400 border-blue-400/50 bg-blue-400/10';
        case 'queued': return 'text-yellow-400 border-yellow-400/50 bg-yellow-400/10';
        default: return 'text-gray-400 border-gray-400/50 bg-gray-400/10';
      }
    } catch (error) {
      logError('getJobStatusColor', error, { status });
      return 'text-gray-400 border-gray-400/50 bg-gray-400/10';
    }
  }, []);

  // Debug panel component
  const DebugPanel = () => {
    if (!debugMode) return null;
    
    return (
      <Card className="mb-6 border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
        <CardHeader>
          <CardTitle className="text-yellow-700 dark:text-yellow-300">Debug Information</CardTitle>
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
            <Button 
              size="sm" 
              onClick={() => {
                localStorage.removeItem('debugLogs');
                setErrors([]);
              }}
            >
              Clear Debug Logs
            </Button>
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
      
      // Immediate job update on component mount
      setTimeout(() => {
        pollJobUpdates();
      }, 1500);
      
      // Poll for job updates every 3 seconds (increased to reduce load)
      const interval = setInterval(pollJobUpdates, 3000);
      return () => clearInterval(interval);
    } catch (error) {
      logError('MyProjectsScreen', error, 'Component mount error');
    }
  }, [loadActiveJobs, loadProjects, loadBacklogJobs, pollJobUpdates]);

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

            {/* Backlog Jobs Section */}
            {backlogJobs.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                  BACKLOG GENERATION HISTORY
                </h2>
                <div className="space-y-4">
                  {backlogJobs.map((job) => (
                    <Card key={job.id} className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <FiFolder className="w-5 h-5 text-primary glow-cyan" />
                            <div>
                              <CardTitle className="text-foreground glow-cyan">
                                {job.project_name}
                              </CardTitle>
                              <p className="text-sm text-muted-foreground font-mono">
                                Job ID: {job.id}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant="outline" 
                              className="font-mono text-green-400 border-green-400/50 bg-green-400/10"
                            >
                              {job.status?.toUpperCase() || 'COMPLETED'}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteBacklogJob(job.id)}
                              className="text-red-400 hover:text-red-300"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-muted-foreground mb-2">
                          <div>Epics: <span className="text-foreground font-semibold">{job.epics_generated}</span></div>
                          <div>Features: <span className="text-foreground font-semibold">{job.features_generated}</span></div>
                          <div>User Stories: <span className="text-foreground font-semibold">{job.user_stories_generated}</span></div>
                          <div>Tasks: <span className="text-foreground font-semibold">{job.tasks_generated}</span></div>
                          <div>Test Cases: <span className="text-foreground font-semibold">{job.test_cases_generated}</span></div>
                          <div>Exec Time: <span className="text-foreground font-semibold">{job.execution_time_seconds ? `${job.execution_time_seconds.toFixed(1)}s` : 'N/A'}</span></div>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Created: {new Date(job.created_at).toLocaleString()}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Projects Section */}
            <div>
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                PROJECTS
              </h2>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-muted-foreground mt-2">Loading projects...</p>
                </div>
              ) : projects.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {projects.map((project) => (
                    <Card 
                      key={project.id}
                      className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-primary/60 hover:glow-cyan transition-all duration-300 cursor-pointer"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <FiFolder className="w-6 h-6 text-primary glow-cyan" />
                          <Badge variant="outline" className="text-xs">
                            {project.status}
                          </Badge>
                        </div>
                        <CardTitle className="text-xl font-semibold text-foreground glow-cyan">
                          {project.basics?.name || 'Untitled Project'}
                        </CardTitle>
                      </CardHeader>
                      
                      <CardContent>
                        <p className="text-muted-foreground mb-4 text-sm">
                          {project.basics?.description || 'No description available'}
                        </p>
                        
                        <div className="text-xs text-muted-foreground space-y-1">
                          <div>Domain: {project.basics?.domain || 'Unknown'}</div>
                          <div>Created: {new Date(project.createdAt).toLocaleDateString()}</div>
                          <div>Updated: {new Date(project.updatedAt).toLocaleDateString()}</div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                  <CardContent className="pt-6 text-center">
                    <FiFolder className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-foreground mb-2">No Projects Found</h3>
                    <p className="text-muted-foreground mb-4">
                      Create your first project to get started with backlog automation.
                    </p>
                    <Button
                      onClick={() => navigate('/simple-project-wizard')}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground"
                    >
                      <FiFolder className="w-4 h-4 mr-2" />
                      Create New Project
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyProjectsScreen;
