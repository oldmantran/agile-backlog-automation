import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { FiPlay, FiInfo, FiArrowRight, FiGlobe } from 'react-icons/fi';

const NewProjectScreen: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{success?: boolean, message?: string, projectId?: string} | null>(null);

  const handleFormSubmit = async (projectData: any) => {
    setIsSubmitting(true);
    setSubmitStatus(null);
    
    try {
      console.log('🚀 Submitting project data:', projectData);
      
      // Submit directly to generate-backlog endpoint
      const response = await fetch('/api/generate-backlog', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData),
      });

      const result = await response.json();
      console.log('📤 API Response:', result);

      if (result.success && result.data) {
        setSubmitStatus({
          success: true,
          message: `Project created successfully! Job ID: ${result.data.jobId}`,
          projectId: result.data.projectId
        });
        
        // Store the active job in localStorage for MyProjectsScreen to track
        const activeJob = {
          jobId: result.data.jobId,
          projectName: projectData.projectName || 'New Project',
          startTime: new Date().toISOString(),
          status: 'running',
          progress: 0,
          currentAction: 'Initializing...'
        };
        
        const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
        existingJobs.push(activeJob);
        localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
        
        // Navigate to My Projects page where progress is displayed
        setTimeout(() => {
          navigate('/my-projects');
        }, 2000);
      } else {
        setSubmitStatus({
          success: false,
          message: result.message || 'Failed to create project. Please try again.'
        });
      }
    } catch (error) {
      console.error('Error submitting project:', error);
      setSubmitStatus({
        success: false,
        message: 'Network error. Please check your connection and try again.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-y-auto">
          <div className="bg-gradient-to-br from-background via-background to-primary/5 min-h-full">
            <div className="relative overflow-hidden">
              {/* Animated background elements */}
              <div className="absolute inset-0 opacity-15">
                <div className="scan-line absolute w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent"></div>
              </div>

              <div className="relative z-10 container mx-auto px-6 py-8">
                {/* Header */}
                <div className="mb-8">
                  <div className="flex items-center space-x-3 mb-4">
                    <FiPlay className="w-8 h-8 text-primary glow-cyan" />
                    <h1 className="text-4xl font-bold text-foreground tracking-wider glow-cyan">
                      CREATE NEW PROJECT
                    </h1>
                  </div>
                  <p className="text-muted-foreground text-lg">
                    Transform your product vision into a comprehensive Azure DevOps backlog with AI-powered domain intelligence
                  </p>
                </div>

                {/* Quick Info */}
                <Alert className="mb-6 border-blue-500/50 bg-blue-500/10">
                  <FiInfo className="w-4 h-4" />
                  <AlertDescription className="text-blue-300 text-sm">
                    <strong>AI-Powered Generation:</strong> Choose domain intelligence and testing options to customize your backlog generation.
                  </AlertDescription>
                </Alert>

                {/* Compact Form Container */}
                <div className="max-w-4xl mx-auto">
                  <SimplifiedProjectForm 
                    onSubmit={handleFormSubmit} 
                    isSubmitting={isSubmitting}
                    initialData={{}} 
                  />
                </div>

                {/* Status Display */}
                {submitStatus && (
                  <div className="mt-6 max-w-4xl mx-auto">
                    <Alert className={submitStatus.success ? "border-green-500/50 bg-green-500/10" : "border-red-500/50 bg-red-500/10"}>
                      <FiInfo className="w-4 h-4" />
                      <AlertDescription className={submitStatus.success ? "text-green-300" : "text-red-300"}>
                        {submitStatus.message}
                        {submitStatus.success && submitStatus.projectId && (
                          <div className="mt-2">
                            <Button 
                              onClick={() => navigate(`/project/${submitStatus.projectId}/generation`)}
                              className="mt-2"
                            >
                              View Generation Progress <FiArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                          </div>
                        )}
                      </AlertDescription>
                    </Alert>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default NewProjectScreen;