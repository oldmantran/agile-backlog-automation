import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import { FiX } from 'react-icons/fi';

const SimpleProjectWizard: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      console.log('🚀 Starting project submission with data:', projectData);
      setError(null);
      
      // Step 1: Create the project
      console.log('📞 Calling createProject API...');
      
      const projectResponse = await projectApi.createProject(projectData);
      console.log('✅ Project creation response:', projectResponse);
      console.log('📊 Response type:', typeof projectResponse);
      console.log('📊 Response keys:', Object.keys(projectResponse || {}));
      console.log('📊 Full response object:', JSON.stringify(projectResponse, null,2));
      
      // Handle different response formats
      let projectId;
      if (projectResponse && typeof projectResponse === 'object') {
        // The response interceptor should have unwrapped the data
        projectId = projectResponse.projectId;
        console.log('Extracted projectId:', projectId);
        
        // Try alternative locations if projectId is not found
        if (!projectId) {
          console.log('projectId not found at root level, trying alternatives...');
          const response = projectResponse as any;
          projectId = response.data?.projectId || response.id;
          console.log('Alternative projectId:', projectId);
        }
      }
      
      if (projectId) {
        console.log('🎯 Found projectId:', projectId);
        // Step 2: Start backlog generation
        console.log('📞 Calling generateBacklog API for project:', projectId);
        
        try {
          const backlogResponse = await backlogApi.generateBacklog(projectId);
          console.log('✅ Backlog generation response:', backlogResponse);
          
          if (backlogResponse.jobId) {
            console.log('🎯 Found jobId:', backlogResponse.jobId);
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
            
            console.log('💾 Storing job info:', jobInfo);
            const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
            existingJobs.push(jobInfo);
            localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
            
            // Navigate immediately to My Projects screen
            console.log('🧭 Navigating to My Projects screen...');
            navigate('/my-projects');
            
          } else {
            console.error('❌ No jobId in backlog response:', backlogResponse);
            throw new Error('Failed to start backlog generation - no job ID returned');
          }
        } catch (backlogError) {
          console.error('❌ Backlog generation error:', backlogError);
          throw new Error(`Failed to start backlog generation: ${backlogError instanceof Error ? backlogError.message : 'Unknown error'}`);
        }
      } else {
        console.error('❌ No projectId found in project response:', projectResponse);
        throw new Error('Failed to create project - no project ID returned');
      }
    } catch (error) {
      console.error('Project creation error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project';
      setError(errorMessage);
    }
  };

  const handleBackToHome = () => {
    console.log('Navigating back to dashboard...');
    try {
      navigate('/my-projects');
    } catch (error) {
      console.error('React Router navigation failed:', error);
      // Fallback to direct navigation
      window.location.href = '/my-projects';
    }
  };

  const handleRestart = () => {
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

        {!error && (
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
              isSubmitting={false}
            />
          </>
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