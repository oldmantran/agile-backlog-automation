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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [jobInfo, setJobInfo] = useState<any>(null);

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      console.log('🚀 Starting project submission with data:', projectData);
      setError(null);
      setIsSubmitting(true);
      
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
            
            // Show success state
            setJobInfo(jobInfo);
            setIsSuccess(true);
            setIsSubmitting(false);
            
            console.log('✅ Backlog generation started successfully!');
            
            // Navigate to My Projects screen after a brief delay
            setTimeout(() => {
              console.log('🧭 Navigating to My Projects screen...');
              try {
                navigate('/my-projects');
                console.log('✅ React Router navigation successful');
              } catch (navError) {
                console.error('❌ React Router navigation failed:', navError);
                console.log('🔄 Falling back to window.location navigation...');
                window.location.href = '/my-projects';
              }
            }, 2000); // 2 second delay to show success message
            
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
    } finally {
      setIsSubmitting(false);
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

        {!error && !isSuccess && (
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

        {isSuccess && jobInfo && (
          <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CardContent className="pt-6">
              <div className="space-y-6 text-center">
                <div className="flex justify-center">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-green-700 dark:text-green-300 mb-2">
                    Backlog Generation Started!
                  </h2>
                  <p className="text-green-600 dark:text-green-400 mb-4">
                    Your project "{jobInfo.projectName}" has been created and backlog generation is now running.
                  </p>
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg text-sm">
                    <div className="grid grid-cols-2 gap-4 text-left">
                      <div>
                        <span className="font-semibold">Project ID:</span> {jobInfo.projectId}
                      </div>
                      <div>
                        <span className="font-semibold">Job ID:</span> {jobInfo.jobId}
                      </div>
                      <div>
                        <span className="font-semibold">Status:</span> {jobInfo.status}
                      </div>
                      <div>
                        <span className="font-semibold">Current Action:</span> {jobInfo.currentAction}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-green-600 dark:text-green-400 mt-4">
                    Redirecting to My Projects screen to monitor progress...
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