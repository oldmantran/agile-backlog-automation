import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Alert, AlertDescription } from '../../components/ui/alert';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { backlogApi } from '../../services/api/backlogApi';
import { projectApi } from '../../services/api/projectApi';
import { Project } from '../../types/project';
import { 
  FiPlus, 
  FiFolder, 
  FiActivity, 
  FiRefreshCw, 
  FiClock,
  FiCheckCircle,
  FiXCircle,
  FiInfo,
  FiTrash2
} from 'react-icons/fi';

interface JobInfo {
  jobId: string;
  projectName: string;
  startTime: string;
  status?: string;
  progress?: number;
  currentAction?: string;
  error?: string;
}

const MyProjectsScreen: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState<JobInfo[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActiveJobs();
    loadProjects();
    // Poll for job updates every 5 seconds
    const interval = setInterval(pollJobUpdates, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadActiveJobs = () => {
    const stored = localStorage.getItem('activeJobs');
    if (stored) {
      const jobs = JSON.parse(stored);
      setActiveJobs(jobs);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await projectApi.listProjects(1, 20);
      setProjects(response.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollJobUpdates = async () => {
    const stored = localStorage.getItem('activeJobs');
    if (!stored) return;

    const jobs: JobInfo[] = JSON.parse(stored);
    const updatedJobs: JobInfo[] = [];

    for (const job of jobs) {
      try {
        const status = await backlogApi.getGenerationStatus(job.jobId);
        
        const updatedJob = {
          ...job,
          status: status.status,
          progress: status.progress || 0,
          currentAction: status.currentAction || `${status.currentAgent} working...`,
          error: status.error
        };

        // Only keep jobs that are still running or recently completed
        if (status.status === 'running' || status.status === 'queued' || 
            (status.status === 'completed' && Date.now() - new Date(job.startTime).getTime() < 300000) || // 5 minutes
            (status.status === 'failed' && Date.now() - new Date(job.startTime).getTime() < 300000)) {
          updatedJobs.push(updatedJob);
        }
      } catch (error) {
        // Keep job if we can't check status (might be temporary API issue)
        if (Date.now() - new Date(job.startTime).getTime() < 300000) { // 5 minutes
          updatedJobs.push(job);
        }
      }
    }

    setActiveJobs(updatedJobs);
    localStorage.setItem('activeJobs', JSON.stringify(updatedJobs));
  };

  const removeJob = (jobId: string) => {
    const updated = activeJobs.filter(job => job.jobId !== jobId);
    setActiveJobs(updated);
    localStorage.setItem('activeJobs', JSON.stringify(updated));
  };

  const getJobStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed': return <FiCheckCircle className="w-5 h-5 text-green-400" />;
      case 'failed': return <FiXCircle className="w-5 h-5 text-red-400" />;
      case 'running': return <FiActivity className="w-5 h-5 text-blue-400 animate-pulse" />;
      case 'queued': return <FiClock className="w-5 h-5 text-yellow-400" />;
      default: return <FiActivity className="w-5 h-5 text-gray-400" />;
    }
  };

  const getJobStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 border-green-400/50 bg-green-400/10';
      case 'failed': return 'text-red-400 border-red-400/50 bg-red-400/10';
      case 'running': return 'text-blue-400 border-blue-400/50 bg-blue-400/10';
      case 'queued': return 'text-yellow-400 border-yellow-400/50 bg-yellow-400/10';
      default: return 'text-gray-400 border-gray-400/50 bg-gray-400/10';
    }
  };

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
                  <p className="text-muted-foreground text-lg">
                    Manage your backlog automation projects and monitor active generation jobs
                  </p>
                </div>
                <Button 
                  onClick={() => navigate('/new-project')}
                  className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
                >
                  <FiPlus className="w-4 h-4 mr-2" />
                  New Project
                </Button>
              </div>
            </div>

            {/* Active Jobs Widget */}
            {activeJobs.length > 0 && (
              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <FiActivity className="w-5 h-5 text-primary glow-cyan" />
                    <CardTitle className="text-foreground glow-cyan">Active Generation Jobs</CardTitle>
                    <Badge variant="outline" className="bg-primary/20 text-primary border-primary/50">
                      {activeJobs.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {activeJobs.map((job) => (
                      <div key={job.jobId} className="p-4 rounded-lg bg-background/50 border border-primary/20">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            {getJobStatusIcon(job.status)}
                            <div>
                              <h4 className="font-medium text-foreground glow-cyan">{job.projectName}</h4>
                              <p className="text-sm text-muted-foreground">Job ID: {job.jobId}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge className={getJobStatusColor(job.status)}>
                              {(job.status || 'unknown').toUpperCase()}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeJob(job.jobId)}
                              className="h-8 w-8 p-0 hover:bg-red-500/20"
                            >
                              <FiTrash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        
                        {job.status === 'running' && (
                          <>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-muted-foreground">
                                {job.currentAction || 'Processing...'}
                              </span>
                              <span className="text-sm text-primary font-mono">
                                {Math.round(job.progress || 0)}%
                              </span>
                            </div>
                            <Progress 
                              value={job.progress || 0} 
                              className="h-2 glow-cyan" 
                            />
                          </>
                        )}

                        {job.status === 'completed' && (
                          <div className="flex items-center text-green-400 text-sm">
                            <FiCheckCircle className="w-4 h-4 mr-2" />
                            Backlog generation completed successfully!
                          </div>
                        )}

                        {job.status === 'failed' && job.error && (
                          <div className="flex items-start text-red-400 text-sm">
                            <FiXCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                            <span>{job.error}</span>
                          </div>
                        )}
                        
                        <div className="text-xs text-muted-foreground mt-2">
                          Started: {new Date(job.startTime).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Projects Grid */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">
                YOUR PROJECTS
              </h2>
              
              {loading ? (
                <div className="text-center py-8">
                  <FiRefreshCw className="w-8 h-8 text-primary animate-spin mx-auto mb-4" />
                  <p className="text-muted-foreground">Loading projects...</p>
                </div>
              ) : projects.length === 0 ? (
                <Alert className="tron-card">
                  <FiInfo className="w-4 h-4" />
                  <AlertDescription>
                    No projects found. Create your first project to get started with backlog automation.
                  </AlertDescription>
                </Alert>
              ) : (
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
                          {project.basics.name}
                        </CardTitle>
                      </CardHeader>
                      
                      <CardContent>
                        <p className="text-muted-foreground mb-4 text-sm">
                          {project.basics.description}
                        </p>
                        
                        <div className="text-xs text-muted-foreground space-y-1">
                          <div>Domain: {project.basics.domain}</div>
                          <div>Created: {new Date(project.createdAt).toLocaleDateString()}</div>
                          <div>Updated: {new Date(project.updatedAt).toLocaleDateString()}</div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyProjectsScreen;
