import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import { FiArrowLeft, FiCheckCircle, FiX } from 'react-icons/fi';

const SimpleProjectWizard: React.FC = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      console.log('Starting project submission with data:', projectData);
      setIsSubmitting(true);
      setError(null);
      
      // Step 1: Create the project
      console.log('Calling createProject API...');
      
      const projectResponse = await projectApi.createProject(projectData);
      console.log('Project creation response:', projectResponse);
      
      // Handle different response formats
      let projectId;
      if (projectResponse && typeof projectResponse === 'object') {
        projectId = projectResponse.projectId || projectResponse.data?.projectId || projectResponse.id;
      }
      
      if (projectId) {
        console.log('Found projectId:', projectId);
        // Step 2: Start backlog generation
        console.log('Calling generateBacklog API for project:', projectId);
        
        const backlogResponse = await backlogApi.generateBacklog(projectId);
        console.log('Backlog generation response:', backlogResponse);
        
        if (backlogResponse.jobId) {
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
          
          // Navigate immediately to My Projects screen
          console.log('Navigating to My Projects screen...');
          navigate('/projects');
          
        } else {
          console.error('No jobId in backlog response:', backlogResponse);
          throw new Error('Failed to start backlog generation - no job ID returned');
        }
      } else {
        console.error('No projectId found in project response:', projectResponse);
        throw new Error('Failed to create project - no project ID returned');
      }
    } catch (error) {
      console.error('Project creation error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project';
      setError(errorMessage);
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
    setError(null);
  };

  const handleRestart = () => {
    setIsSubmitting(false);
    setError(null);
  };

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <div className="space-y-8">
        <div className="text-center">
          <h1 className="text-3 font-bold mb-4">
            Agile Backlog Automation
          </h1>
          <p className="text-lg text-muted-foreground">
            Transform your product vision into a comprehensive backlog with AI-powered automation
          </p>
        </div>

        {!isSubmitting && !error && (
          <>
            <Alert className="rounded-md">
              <AlertDescription>
                <div>
                  <h4 className="font-bold mb-1">Simplified Setup</h4>
                  <p>
                    Only 4s required: Vision Statement, Azure DevOps Project, Area Path, and Iteration Path. 
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
          <Card className="bg-blue-50 bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardContent className="pt-6">
              <div className="space-y-6 text-center">
                <div className="flex justify-center">
                  <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-blue-700 dark:text-blue-300 mb-2">
                    Setting Up Your Project
                  </h2>
                  <p className="text-blue-600 dark:text-blue-400">
                    Creating project and starting backlog generation...
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="bg-red-50 bg-red-950 border-red-200 dark:border-red-800">
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
      </div>
    </div>
  );
};

export default SimpleProjectWizard; 