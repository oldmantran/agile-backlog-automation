import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
// Note: Using title attribute for tooltips instead of custom Tooltip component
import { FiActivity, FiCheckCircle, FiXCircle, FiClock, FiTrash2, FiAlertTriangle, FiFolder, FiRotateCcw, FiCalendar, FiBarChart, FiFileText, FiInfo } from 'react-icons/fi';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { BacklogJob } from '../../types/backlogJob';
import { Project } from '../../types/project';
import { useHybridProgress } from '../../hooks/useHybridProgress';

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
  // Simple alert-based feedback instead of toast for now
  const showAlert = (title: string, message: string, type: 'success' | 'error' = 'success') => {
    alert(`${title}: ${message}`);
  };

  // Parse staging summary from raw_summary
  const getStagingSummary = () => {
    try {
      const rawSummary = job.raw_summary as any;
      return rawSummary?.staging_summary || {};
    } catch {
      return {};
    }
  };

  // Parse Azure DevOps configuration from raw_summary
  const getAzureConfig = () => {
    try {
      const rawSummary = job.raw_summary as any;
      
      // Try multiple possible locations for Azure config
      if (rawSummary?.azure_config) {
        return rawSummary.azure_config;
      }
      if (rawSummary?.metadata?.azure_config) {
        return rawSummary.metadata.azure_config;
      }
      
      // Try constructing from ado_summary or azure_integration
      const adoSummary = rawSummary?.ado_summary || rawSummary?.azure_integration || {};
      if (adoSummary.project || adoSummary.area_path) {
        return {
          project: adoSummary.project,
          areaPath: adoSummary.area_path || adoSummary.areaPath,
          iterationPath: adoSummary.iteration_path || adoSummary.iterationPath
        };
      }
      
      return {};
    } catch {
      return {};
    }
  };

  const getUploadMetrics = () => {
    const stagingSummary = getStagingSummary();
    const byStatus = stagingSummary.by_status || {};
    
    // Calculate total generated including all work item types
    const totalGenerated = (job.epics_generated || 0) + 
                          (job.features_generated || 0) + 
                          (job.user_stories_generated || 0) + 
                          (job.tasks_generated || 0) + 
                          (job.test_cases_generated || 0) + 
                          (job.test_plans_generated || 0);
    
    // For older projects without staging data, estimate from Azure DevOps summary
    let totalUploaded = byStatus.success || 0;
    let totalFailed = byStatus.failed || 0;
    let totalSkipped = byStatus.skipped || 0;
    let uploadDataAvailable = !!stagingSummary.total_items;
    
    // If no staging data available, try to get from Azure DevOps summary
    if (!uploadDataAvailable && job.raw_summary) {
      try {
        const rawSummary = job.raw_summary as any;
        const adoSummary = rawSummary.ado_summary || rawSummary.azure_integration || {};
        
        if (adoSummary.total_created !== undefined) {
          totalUploaded = adoSummary.total_created || 0;
          totalFailed = Math.max(0, totalGenerated - totalUploaded);
          uploadDataAvailable = true;
        } else if (adoSummary.work_items_created) {
          // Handle newer format with work_items_created array
          totalUploaded = adoSummary.work_items_created.length || 0;
          totalFailed = Math.max(0, totalGenerated - totalUploaded);
          uploadDataAvailable = true;
        } else {
          // Check for upload count in the email notification pattern
          const uploadNote = job.status?.match(/only (\d+) items made it into ADO/);
          if (uploadNote && uploadNote[1]) {
            totalUploaded = parseInt(uploadNote[1]);
            totalFailed = Math.max(0, totalGenerated - totalUploaded);
            uploadDataAvailable = true;
          }
        }
      } catch (e) {
        console.warn('Failed to parse upload metrics:', e);
      }
    }
    
    // If no upload data is available, don't assume failure
    if (!uploadDataAvailable && totalGenerated > 0) {
      // Check if this is a content-only generation (no Azure DevOps integration)
      const azureConfig = getAzureConfig();
      const hasAzureConfig = azureConfig.project && azureConfig.areaPath;
      
      if (!hasAzureConfig) {
        // Content-only generation - no upload expected
        totalUploaded = 0;
        totalFailed = 0;
        totalSkipped = 0;
      } else {
        // Expected upload but no data - mark as unknown status rather than failed
        totalUploaded = 0;
        totalFailed = 0;
        totalSkipped = 0;
      }
    }
    
    const failureRate = totalGenerated > 0 ? ((totalFailed + totalSkipped) / totalGenerated) * 100 : 0;
    
    return {
      totalGenerated,
      totalUploaded,
      totalFailed,
      totalSkipped,
      failureRate: Math.round(failureRate * 10) / 10,
      hasFailures: totalFailed > 0 || totalSkipped > 0,
      uploadDataAvailable
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
  
  // Robust staging job ID resolution
  const getJobIdInfo = () => {
    try {
      const rawSummary = job.raw_summary as any;
      
      // Prefer authoritative raw_summary.job_id
      if (rawSummary?.job_id) {
        return {
          jobId: rawSummary.job_id,
          source: 'authoritative',
          canRetry: true
        };
      }
      
      if (rawSummary?.metadata?.job_id) {
        return {
          jobId: rawSummary.metadata.job_id,
          source: 'metadata',
          canRetry: true
        };
      }
      
      // Fallback to timestamp-based ID - but this cannot be retried reliably
      if (job.created_at) {
        const timestamp = new Date(job.created_at).toISOString().replace(/[:\-T]/g, '').slice(0, 15);
        return {
          jobId: `job_${timestamp}`,
          source: 'timestamp_fallback',
          canRetry: false
        };
      }
      
      return {
        jobId: `job_${job.id || 'unknown'}`,
        source: 'database_fallback',
        canRetry: false
      };
    } catch {
      return {
        jobId: `job_${job.id || 'unknown'}`,
        source: 'error_fallback',
        canRetry: false
      };
    }
  };
  
  const jobIdInfo = getJobIdInfo();
  const azureConfig = getAzureConfig();
  
  // Check if Azure config is complete for retry operations
  const getAzureConfigStatus = () => {
    const requiredFields = ['organizationUrl', 'project', 'personalAccessToken', 'areaPath', 'iterationPath'];
    const missingFields = requiredFields.filter(field => !azureConfig[field]);
    
    return {
      isComplete: missingFields.length === 0,
      missingFields,
      hasBasicConfig: azureConfig.project && azureConfig.areaPath
    };
  };
  
  const azureConfigStatus = getAzureConfigStatus();
  
  // Use Azure DevOps project name as the title, with area path as subtitle
  const getDisplayInfo = () => {
    const azureConfig = getAzureConfig();
    
    // Use ADO project name as the main title
    const title = azureConfig.project || job.project_name || 'Unknown Project';
    
    // Use area path as subtitle if available and different from project name
    let subtitle = azureConfig.areaPath || azureConfig.area_path || null;
    
    // Don't show area path if it's the same as project name or empty
    if (subtitle === title || !subtitle || subtitle.trim() === '') {
      subtitle = null;
    }
    
    return { title, subtitle };
  };
  
  const { title: projectDisplayName, subtitle: areaPathSubtitle } = getDisplayInfo();

  // Temporary debugging for "Test Project" 
  if (job.project_name === 'Test Project') {
    console.log('=== Test Project Debug Data ===');
    console.log('Basic job info:', {
      database_id: job.id,
      stored_project_name: job.project_name,
      calculated_display_name: projectDisplayName,
      calculated_job_id: job.id,
      created_at: job.created_at
    });
    console.log('Raw summary structure:', job.raw_summary);
    console.log('Azure config extracted:', azureConfig);
    console.log('Staging summary:', getStagingSummary());
    console.log('Upload metrics:', metrics);
    console.log('=== End Debug Data ===');
  }

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
              {projectDisplayName}
            </CardTitle>
            {areaPathSubtitle && (
              <p className="text-sm text-blue-400 font-medium mt-1">
                {areaPathSubtitle}
              </p>
            )}
            <div className="flex items-center space-x-2 mt-2 text-xs text-muted-foreground font-mono">
              <FiCalendar className="w-3 h-3" />
              <span>{date} at {time}</span>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <p className="text-xs text-muted-foreground font-mono">
                Job ID: {jobIdInfo.jobId.length > 20 ? `${jobIdInfo.jobId.substring(0, 20)}...` : jobIdInfo.jobId}
              </p>
              {jobIdInfo.source !== 'authoritative' && (
                <FiInfo 
                  className="w-3 h-3 text-yellow-500" 
                  title={`Job ID from ${jobIdInfo.source.replace('_', ' ')} - ${jobIdInfo.canRetry ? 'retry may work' : 'retry not possible'}`}
                />
              )}
            </div>
          </div>
          <Badge 
            variant={job.status === 'completed' ? 'default' : job.status === 'failed' ? 'destructive' : 'secondary'}
            className="font-mono text-xs"
          >
            {job.status?.toUpperCase() || 'UNKNOWN'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Generation Summary */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm font-medium">
            <FiBarChart className="w-4 h-4 text-primary" />
            <span>Generation Summary</span>
            {metrics.uploadDataAvailable && (
              <FiInfo 
                className="w-3 h-3 text-blue-500 cursor-help" 
                title="Detailed staging breakdown available in the detailed view"
              />
            )}
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
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-center">
              <div className="text-muted-foreground">Epics</div>
              <div className="font-mono font-semibold">{job.epics_generated || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Features</div>
              <div className="font-mono font-semibold">{job.features_generated || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Stories</div>
              <div className="font-mono font-semibold">{job.user_stories_generated || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Tasks</div>
              <div className="font-mono font-semibold">{job.tasks_generated || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Test Cases</div>
              <div className="font-mono font-semibold">{job.test_cases_generated || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Test Plans</div>
              <div className="font-mono font-semibold">{job.test_plans_generated || 0}</div>
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
            {metrics.hasFailures && (
              <div className="text-xs text-orange-600 bg-orange-50 dark:bg-orange-950 px-2 py-1 rounded">
                ⚠️ {metrics.totalFailed + (metrics.totalSkipped || 0)} items failed to upload - click retry button below
              </div>
            )}
          </div>
        </div>

        {/* Azure Config Warning */}
        {azureConfigStatus.hasBasicConfig && !azureConfigStatus.isComplete && (
          <div className="flex items-center space-x-2 p-2 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded text-xs">
            <FiAlertTriangle className="w-3 h-3 text-yellow-600" />
            <span className="text-yellow-700 dark:text-yellow-300">
              Incomplete Azure config - missing: {azureConfigStatus.missingFields.join(', ')}
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center pt-2 border-t border-border">
          <div className="flex space-x-2">
            {/* Only show retry button if there are actual failures with upload data available */}
            {metrics.hasFailures && metrics.uploadDataAvailable && jobIdInfo.canRetry && azureConfigStatus.isComplete ? (
              <Button
                size="sm"
                variant={isRetrying ? "outline" : "default"}
                onClick={async () => {
                  try {
                    await onRetry();
                    // Success alert will be handled by the parent component
                  } catch (error) {
                    showAlert(
                      "Retry Failed",
                      error instanceof Error ? error.message : "Unknown error occurred"
                    );
                  }
                }}
                disabled={isRetrying}
                className={`text-xs ${!isRetrying ? 'bg-orange-500 hover:bg-orange-600 text-white' : ''}`}
                title={`Retry uploading ${metrics.totalFailed + metrics.totalSkipped} failed work items to Azure DevOps`}
              >
                {isRetrying ? (
                  <FiActivity className="w-3 h-3 mr-1 animate-spin" />
                ) : (
                  <FiRotateCcw className="w-3 h-3 mr-1" />
                )}
                {isRetrying ? 'Retrying...' : 'Retry Failed Uploads'}
              </Button>
            ) : metrics.hasFailures && metrics.uploadDataAvailable && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  let message = "Cannot retry uploads.";
                  if (!jobIdInfo.canRetry) {
                    message += " No authoritative job ID found. Please run a new job with Azure DevOps enabled.";
                  } else if (!azureConfigStatus.isComplete) {
                    message += ` Missing Azure configuration: ${azureConfigStatus.missingFields.join(', ')}.`;
                  }
                  showAlert("Retry Not Available", message);
                }}
                disabled
                className="text-xs opacity-50 cursor-not-allowed"
                title="Retry not possible - check job ID or Azure configuration"
              >
                <FiRotateCcw className="w-3 h-3 mr-1" />
                Retry Unavailable
              </Button>
            )}
            {/* Add Test Artifacts button - only show if test artifacts weren't included originally */}
            {(() => {
              try {
                const rawSummary = typeof job.raw_summary === 'string' ? JSON.parse(job.raw_summary) : job.raw_summary;
                const testArtifactsIncluded = rawSummary?.test_artifacts_included;
                return !testArtifactsIncluded && job.status === 'completed';
              } catch {
                return false;
              }
            })() && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  try {
                    // Extract project ID from job data
                    const rawSummary = typeof job.raw_summary === 'string' ? JSON.parse(job.raw_summary) : job.raw_summary;
                    const projectId = rawSummary?.project_id || jobIdInfo.jobId.split('_').pop() || '';
                    if (!projectId) {
                      console.error('No project ID found for test generation');
                      return;
                    }
                    
                    const response = await fetch(`/api/projects/${projectId}/generate-test-artifacts`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (!response.ok) {
                      const error = await response.json();
                      console.error('Failed to start test generation:', error.detail);
                      return;
                    }
                    
                    const result = await response.json();
                    console.log('Test generation started:', result);
                    
                    // Navigate to the progress view or show a notification
                    if (result.data?.jobId) {
                      window.location.href = `/generation-progress?jobId=${result.data.jobId}`;
                    }
                  } catch (error) {
                    console.error('Error starting test generation:', error);
                  }
                }}
                className="text-xs"
                title="Generate test plans, test suites, and test cases for this project"
              >
                <FiFileText className="w-3 h-3 mr-1" />
                Add Testing
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
  
  // Hybrid progress hook for real-time updates with polling fallback
  const { lastUpdate: progressUpdate, error: progressError, connectionType, connect: connectProgress, disconnect: disconnectProgress } = useHybridProgress();

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
    // Simple alert-based feedback instead of toast for now
    const showAlert = (title: string, message: string) => alert(`${title}: ${message}`);
    
    try {
      const jobId = job.id;
      setRetryingJobs(prev => new Set([...Array.from(prev), jobId]));
      
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
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const result = await response.json();
      console.log(`Retry result for job ${jobId}:`, result);
      
      // Show outcome feedback based on structured response
      if (result.success) {
        // Parse success message to extract numbers if available
        const successMatch = result.output?.match(/Successfully recovered (\d+) items/);
        const successCount = successMatch ? parseInt(successMatch[1]) : 0;
        
        showAlert(
          "✅ Retry Successful",
          successCount > 0 
            ? `Successfully recovered ${successCount} work items to Azure DevOps`
            : "Retry operation completed successfully"
        );
      } else {
        throw new Error(result.error || "Retry operation failed");
      }
      
      // Refresh the backlog jobs to get updated status
      await loadBacklogJobs();
      
    } catch (error) {
      // Show error alert with specific error message
      showAlert(
        "❌ Retry Failed",
        error instanceof Error ? error.message : "Unknown error occurred during retry"
      );
      
      logError('handleRetryFailedUploads', error, { jobId: job.id });
      throw error; // Re-throw for the card component to handle
    } finally {
      setRetryingJobs(prev => {
        const updated = new Set(Array.from(prev));
        updated.delete(job.id);
        return updated;
      });
    }
  }, [loadBacklogJobs]);

  // Hybrid progress update handler (SSE + polling fallback)
  const updateJobsFromProgress = useCallback(() => {
    try {
      if (!progressUpdate) return;
      
      const stored = localStorage.getItem('activeJobs');
      if (!stored) {
        return;
      }

      const jobs: JobInfo[] = JSON.parse(stored);
      const updatedJobs: JobInfo[] = [];

      for (const job of jobs) {
        // Check if this progress update is for our job
        if (progressUpdate.jobId === job.jobId) {
          const updatedJob = {
            ...job,
            status: progressUpdate.status || job.status,
            progress: progressUpdate.progress !== undefined ? progressUpdate.progress : (job.progress || 0),
            currentAction: progressUpdate.currentAction || job.currentAction || 'Working...',
            error: progressUpdate.type === 'error' ? progressUpdate.message : job.error
          };
          
          // Only log progress changes
          if (progressUpdate.progress !== job.progress) {
            console.log(`📊 Job ${job.jobId} progress: ${job.progress}% → ${progressUpdate.progress}% (via ${connectionType})`);
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
          // Keep existing job if progress update is for different job
          updatedJobs.push(job);
        }
      }

      setActiveJobs(prev => updatedJobs);
      localStorage.setItem('activeJobs', JSON.stringify(updatedJobs));
    } catch (error) {
      logError('updateJobsFromProgress', error, 'Progress update error');
    }
  }, [progressUpdate, connectionType]);

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

  // Set up hybrid progress connections for active jobs
  useEffect(() => {
    if (activeJobs.length > 0) {
      console.log('🔗 Setting up hybrid progress tracking for active jobs:', activeJobs.map(job => job.jobId));
      
      // Connect to the first active job (we'll handle multiple jobs later)
      const firstJob = activeJobs[0];
      connectProgress(firstJob.jobId);
      
      return () => {
        console.log('🔌 Disconnecting progress tracking');
        disconnectProgress();
      };
    } else {
      // No active jobs, disconnect
      disconnectProgress();
    }
  }, [activeJobs, connectProgress, disconnectProgress]);

  // Effect to handle progress updates from either SSE or polling
  useEffect(() => {
    if (progressUpdate) {
      updateJobsFromProgress();
    }
  }, [progressUpdate]);

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

            {/* Progress Connection Status */}
            {progressError && (
              <Alert className="mb-6 border-orange-500 bg-orange-50 dark:bg-orange-950">
                <FiXCircle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                <AlertDescription className="text-orange-700 dark:text-orange-300">
                  <strong>Progress Tracking ({connectionType}):</strong> {progressError}
                  {connectionType === 'polling' && (
                    <span className="block text-xs mt-1 opacity-75">
                      Switched to polling mode for compatibility
                    </span>
                  )}
                </AlertDescription>
              </Alert>
            )}
            
            {/* Connection Type Indicator for debugging */}
            {process.env.NODE_ENV === 'development' && connectionType !== 'disconnected' && (
              <div className="mb-4 text-xs text-muted-foreground">
                📡 Progress tracking: <span className="font-mono">{connectionType}</span>
                {connectionType === 'polling' && ' (fallback)'}
              </div>
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
                            { (job.progress === undefined || job.progress === null || (job.progress === 0 && (job.status === 'queued' || job.status === 'running'))) ? (
                              <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div className="h-full bg-primary/50 animate-pulse" style={{ width: '100%' }} />
                              </div>
                            ) : (
                              <Progress 
                                value={Math.max(0, Math.min(100, job.progress || 0))} 
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
