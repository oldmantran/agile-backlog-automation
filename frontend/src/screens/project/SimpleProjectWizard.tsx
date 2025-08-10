import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';
import { FiX, FiCheckCircle, FiServer } from 'react-icons/fi';

const SimpleProjectWizard: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);

  const waitForBackend = async (maxAttempts = 10): Promise<boolean> => {
    console.log('🔄 Starting backend connectivity check...');
    for (let i = 0; i < maxAttempts; i++) {
      try {
        console.log(`🔍 [${i + 1}/${maxAttempts}] Checking backend at http://localhost:8000/api/health...`);
        const startTime = Date.now();
        const response = await fetch('http://localhost:8000/api/health');
        const endTime = Date.now();
        const duration = endTime - startTime;
        
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ Backend is ready! Status: ${response.status}, Duration: ${duration}ms, Response:`, data);
          return true;
        } else {
          console.log(`⚠️ Backend responded with status ${response.status} (attempt ${i + 1}/${maxAttempts})`);
        }
      } catch (error) {
        console.log(`⏳ Backend not ready yet (attempt ${i + 1}/${maxAttempts}):`, error);
      }
      // Wait 1 second before next attempt
      console.log(`⏰ Waiting 1 second before next attempt...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.error('❌ Backend not available after maximum attempts');
    return false;
  };

  const handleSubmit = async (projectData: Project) => {
    console.log('🚀 Starting project submission with data:', projectData);
    setIsSubmitting(true);
    setError(null);
    
    // Wait for backend to be ready
    const backendReady = await waitForBackend();
    if (!backendReady) {
      console.error('❌ Backend not available, cannot proceed');
      setError('Backend server is not available. Please ensure the server is running.');
      setIsSubmitting(false);
      return;
    }
    
    try {
      const { projectId } = await projectApi.createProject(projectData);
      console.log('✅ Project creation response:', { projectId });
      
      let backlogResponse: any;
      try {
        // Add timeout to prevent hanging
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Backlog generation timeout')), 300000) // 5 minute timeout
        );
        
        const backlogPromise = backlogApi.generateBacklog(projectId);
        backlogResponse = await Promise.race([backlogPromise, timeoutPromise]);
      } catch (backlogError: unknown) {
        console.warn('⚠️ Backlog error:', backlogError);
        setError('Project created successfully, but backlog generation failed. Please check the backend server logs.');
        setIsSubmitting(false);
        return;
      }
      
      if (backlogResponse.jobId) {
        console.log('🎯 Found jobId:', backlogResponse.jobId);
        setJobId(backlogResponse.jobId);
        
        // Add job to localStorage for progress tracking
        const activeJob = {
          jobId: backlogResponse.jobId,
          projectName: projectData.name,
          startTime: new Date().toISOString(),
          status: 'running',
          progress: 0,
          currentAction: 'Initializing backlog generation...'
        };
        
        // Get existing active jobs or initialize empty array
        const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
        existingJobs.push(activeJob);
        localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
        console.log('📊 Added job to localStorage for progress tracking');
        
        setIsSuccess(true);
        console.log('✅ Job submitted successfully');
      } else {
        console.error('❌ No jobId in response');
        throw new Error('No job ID returned from backlog generation');
      }
    } catch (error: unknown) {
      console.error('Error:', error);
      setError('Failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackToHome = () => {
    console.log('Navigating back to dashboard...');
    try {
      navigate('/');
    } catch (error) {
      console.error('React Router navigation failed:', error);
      // Fallback to direct navigation
      window.location.href = '/';
    }
  };

  const handleRestart = () => {
    setError(null);
    setIsSuccess(false);
    setJobId(null);
  };

  const handleCreateAnother = () => {
    setIsSuccess(false);
    setJobId(null);
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

        {isSuccess && (
          <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CardContent className="pt-6">
              <div className="space-y-6 text-center">
                <div className="flex justify-center">
                  <FiCheckCircle className="h-16 w-16 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-green-700 dark:text-green-300 mb-2">
                    Job Submitted Successfully!
                  </h2>
                  <p className="text-green-600 dark:text-green-400 mb-4">
                    Your backlog generation job has been submitted and is now processing.
                  </p>
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-md">
                    <div className="flex items-center justify-center space-x-2 mb-2">
                      <FiServer className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      <span className="font-mono text-sm text-gray-700 dark:text-gray-300">
                        Job ID: {jobId}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Check the backend server logs for progress updates
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-center space-x-3">
                  <Button 
                    onClick={handleCreateAnother}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Create Another Project
                  </Button>
                  <Button 
                    onClick={handleBackToHome}
                    variant="outline"
                  >
                    Return to Dashboard
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
                    Return to Dashboard
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