import React, { useState } from 'react';
import { Alert, AlertDescription } from '../../components/ui/alert';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';

const SimpleProjectWizard: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      setIsSubmitting(true);
      
      // TODO: Add proper toast notification
      console.log('Creating Project: Setting up your project and generating backlog...');

      // Create the project
      const projectResponse = await projectApi.createProject(projectData);
      
      if (projectResponse.projectId) {
        const { projectId } = projectResponse;
        
        // TODO: Add proper toast notification
        console.log('Project Created: Starting backlog generation...');

        // Start backlog generation
        const backlogResponse = await backlogApi.generateBacklog(projectId);
        
        if (backlogResponse.jobId) {
          // Store job info in localStorage for dashboard
          const jobInfo = {
            jobId: backlogResponse.jobId,
            projectId: projectId,
            status: 'queued',
            progress: 0,
            startTime: new Date().toISOString(),
          };
          
          const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
          existingJobs.push(jobInfo);
          localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
          
          // TODO: Add proper toast notification
          console.log(`Backlog Generation Started: Job ID: ${backlogResponse.jobId}. Check the dashboard for progress.`);
          
          // Redirect to dashboard with job ID
          window.location.href = `/dashboard?job=${backlogResponse.jobId}`;
        } else {
          throw new Error('Failed to start backlog generation');
        }
      } else {
        throw new Error('Failed to create project');
      }
    } catch (error) {
      console.error('Project creation error:', error);
      
      // TODO: Add proper toast notification
      console.error('Error:', error instanceof Error ? error.message : 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
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
      </div>
    </div>
  );
};

export default SimpleProjectWizard;
