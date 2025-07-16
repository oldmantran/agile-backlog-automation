import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Card, CardContent } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import { Button } from '../../components/ui/button';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import { FiArrowLeft, FiCheckCircle, FiX } from 'react-icons/fi';

const SimpleProjectWizard: React.FC = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      console.log('Starting project submission with data:', projectData);
      setIsSubmitting(true);
      setProgress(0);
      setError(null);
      setCurrentOperation('Setting up your project and generating backlog...');
      
      // Step 1: Create the project
      setProgress(20);
      setCurrentOperation('Creating project structure...');
      console.log('Calling createProject API...');
      
      const projectResponse = await projectApi.createProject(projectData);
      console.log('Project creation response:', projectResponse);
      
      if (projectResponse.projectId) {
        const { projectId } = projectResponse;
        
        // Step 2: Start backlog generation
        setProgress(40);
        setCurrentOperation('Starting AI backlog generation...');
        console.log('Calling generateBacklog API for project:', projectId);
        
        const backlogResponse = await backlogApi.generateBacklog(projectId);
        console.log('Backlog generation response:', backlogResponse);
        
        if (backlogResponse.jobId) {
          setJobId(backlogResponse.jobId);
          setProgress(60);
          setCurrentOperation('Backlog generation started successfully!');
          
          // Store job info in localStorage
          const jobInfo = {
            jobId: backlogResponse.jobId,
            projectId: projectId,
            projectName: projectData.basics?.name || 'Untitled Project',
            status: 'queued',
            progress: 0,
            startTime: new Date().toISOString(),
            currentAction: 'Epic Strategist initializing...'
          };
          
          const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
          existingJobs.push(jobInfo);
          localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
          
          // Navigate directly to My Projects screen after brief delay
          setTimeout(() => {
            console.log('Navigating to My Projects screen...');
            navigate('/projects');
          }, 2000);
          
        } else {
          console.error('No jobId in backlog response:', backlogResponse);
          throw new Error('Failed to start backlog generation - no job ID returned');
        }
      } else {
        console.error('No projectId in project response:', projectResponse);
        throw new Error('Failed to create project - no project ID returned');
      }
    } catch (error) {
      console.error('Project creation error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project';
      setError(errorMessage);
      setCurrentOperation(`Error: ${errorMessage}`);
      setIsSubmitting(false); // Only set to false on error
    }
  };

  const handleBackToHome = () => {
    console.log('Navigating back to dashboard...');
    try {
      navigate('/projects');
    } catch (error) {
      console.error('React Router navigation failed:', error);
      // Fallback to direct navigation
      window.location.href = '/projects';
    }
  };

  const handleCancel = () => {
    setIsSubmitting(false);
    setProgress(0);
    setCurrentOperation('');
    setJobId(null);
    setError(null);
  };

  const handleRestart = () => {
    setIsSubmitting(false);
    setProgress(0);
    setCurrentOperation('');
    setJobId(null);
    setError(null);
    setIsCompleted(false);
  };

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <div className="space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">
            Agile Backlog Automation
          </h1>
          <p className="text-lg text-muted-foreground">
            Transform your product vision into a comprehensive backlog with AI-powered automation
          </p>
        </div>

        {!isSubmitting && !isCompleted && !error && (
          <>
            <Alert className="rounded-md">
              <AlertDescription>
                <div>
                  <h4 className="font-bold mb-1">Simplified Setup</h4>
                  <p>
                    Only 4 fields required: Vision Statement, Azure DevOps Project, Area Path, and Iteration Path. 
                    Everything else is automatically extracted by AI or set to sensible defaults.
                  </p>
                </div>
              </AlertDescription>
            </Alert>

            <SimplifiedProjectForm 
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
            />
          </>
        )}

        {isSubmitting && (
          <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardContent className="pt-6">
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-xl font-bold text-blue-700 dark:text-blue-300 mb-2">
                    Generating Your Backlog
                  </h2>
                  <p className="text-blue-600 dark:text-blue-400">
                    AI agents are working on your project...
                  </p>
                </div>
                
                <div className="space-y-3">
                  <Progress value={progress} className="h-4" />
                  <p className="text-sm text-blue-600 dark:text-blue-400 text-center">
                    {currentOperation}
                  </p>
                  {jobId && (
                    <p className="text-xs text-muted-foreground text-center">
                      Job ID: {jobId}
                    </p>
                  )}
                </div>
                
                <div className="flex justify-center">
                  <Button 
                    onClick={handleCancel}
                    variant="outline"
                    className="text-red-600 border-red-300 hover:bg-red-50"
                  >
                    <FiX className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <CardContent className="pt-6">
              <div className="space-y-6 text-center">
                <div className="flex justify-center">
                  <FiX className="h-16 w-16 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-red-700 dark:text-red-300 mb-2">
                    Generation Failed
                  </h2>
                  <p className="text-red-600 dark:text-red-400">
                    {error}
                  </p>
                </div>
                
                <div className="flex justify-center space-x-3">
                  <Button 
                    onClick={handleRestart}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Try Again
                  </Button>
                  <Button 
                    onClick={handleBackToHome}
                    variant="outline"
                  >
                    Back to Dashboard
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {isCompleted && (
          <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CardContent className="pt-6">
              <div className="space-y-6 text-center">
                <div className="flex justify-center">
                  <FiCheckCircle className="h-16 w-16 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-green-700 dark:text-green-300 mb-2">
                    Backlog Generation Complete!
                  </h2>
                  <p className="text-green-600 dark:text-green-400">
                    Your comprehensive backlog has been successfully generated and is ready for use.
                  </p>
                </div>
                
                <div className="space-y-3">
                  <Button 
                    onClick={handleBackToHome}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <FiArrowLeft className="mr-2 h-4 w-4" />
                    View Dashboard
                  </Button>
                  {jobId && (
                    <p className="text-xs text-muted-foreground">
                      Job ID: {jobId} - Check your Azure DevOps project for the generated work items
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SimpleProjectWizard;
