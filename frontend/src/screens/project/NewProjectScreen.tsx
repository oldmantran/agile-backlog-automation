import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
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
      console.log('🚀 Starting backlog generation with enhanced domain strategy:', projectData);
      
      const response = await fetch('/api/generate-backlog', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Backlog generation started successfully:', result);
      
      setSubmitStatus({ 
        success: true, 
        message: 'Backlog generation started successfully!',
        projectId: result.project_id || result.job_id
      });
      
      // Navigate to progress screen after a short delay
      setTimeout(() => {
        if (result.project_id || result.job_id) {
          navigate(`/dashboard/${result.project_id || result.job_id}`);
        } else {
          navigate('/dashboard');
        }
      }, 2000);
      
    } catch (error) {
      console.error('❌ Backlog generation failed:', error);
      setSubmitStatus({ 
        success: false, 
        message: error instanceof Error ? error.message : 'An unexpected error occurred' 
      });
    } finally {
      setIsSubmitting(false);
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
              <div className="flex items-center space-x-3 mb-4">
                <FiRocket className="w-8 h-8 text-primary glow-cyan" />
                <h1 className="text-4xl font-bold text-foreground tracking-wider glow-cyan">
                  CREATE NEW PROJECT
                </h1>
              </div>
              <p className="text-muted-foreground text-lg">
                Transform your product vision into a comprehensive Azure DevOps backlog with AI-powered domain intelligence
              </p>
            </div>

            {/* Enhanced Domain Features Info */}
            <Alert className="mb-8 border-blue-500/50 bg-blue-500/10">
              <FiGlobe className="w-4 h-4" />
              <AlertDescription className="text-blue-300">
                <strong>New Domain Intelligence:</strong> Our enhanced system now supports 31+ industry domains with specialized patterns, user types, and vocabulary. 
                Choose to let AI detect your domain automatically or manually select up to 3 domains for optimal backlog generation.
              </AlertDescription>
            </Alert>

            {/* Domain Features Showcase */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <FiGlobe className="w-5 h-5 text-accent glow-cyan" />
                    <h3 className="font-semibold text-foreground glow-cyan">AI Domain Detection</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Automatically identifies your industry from vision statements using advanced pattern matching across 31 domains.
                  </p>
                  <div className="flex flex-wrap gap-1 mt-3">
                    <Badge variant="outline" className="text-xs">Healthcare</Badge>
                    <Badge variant="outline" className="text-xs">Finance</Badge>
                    <Badge variant="outline" className="text-xs">Real Estate</Badge>
                    <Badge variant="outline" className="text-xs">Oil & Gas</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <FiArrowRight className="w-5 h-5 text-green-400 glow-cyan" />
                    <h3 className="font-semibold text-foreground glow-cyan">Manual Override</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Override AI detection and manually select up to 3 domains with primary/secondary weighting for precise control.
                  </p>
                  <div className="flex flex-wrap gap-1 mt-3">
                    <Badge variant="default" className="text-xs">Primary Domain</Badge>
                    <Badge variant="secondary" className="text-xs">Secondary</Badge>
                    <Badge variant="secondary" className="text-xs">Context</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <FiInfo className="w-5 h-5 text-yellow-400 glow-cyan" />
                    <h3 className="font-semibold text-foreground glow-cyan">Smart Context</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Domain-specific user types, terminology, and work patterns ensure your backlog matches industry standards.
                  </p>
                  <div className="flex flex-wrap gap-1 mt-3">
                    <Badge variant="outline" className="text-xs">User Types</Badge>
                    <Badge variant="outline" className="text-xs">Vocabulary</Badge>
                    <Badge variant="outline" className="text-xs">Patterns</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Status Display */}
            {submitStatus && (
              <Alert className={`mb-8 ${
                submitStatus.success 
                  ? 'border-green-500/50 bg-green-500/10' 
                  : 'border-red-500/50 bg-red-500/10'
              }`}>
                <div className={`flex items-center space-x-2 ${
                  submitStatus.success ? 'text-green-300' : 'text-red-300'
                }`}>
                  {submitStatus.success ? '✅' : '❌'}
                  <AlertDescription>
                    {submitStatus.message}
                    {submitStatus.projectId && (
                      <div className="mt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/dashboard/${submitStatus.projectId}`)}
                          className="border-green-500/50 text-green-300 hover:bg-green-500/20"
                        >
                          View Progress <FiArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                      </div>
                    )}
                  </AlertDescription>
                </div>
              </Alert>
            )}

            {/* Main Form */}
            <div className="flex justify-center">
              <SimplifiedProjectForm 
                onSubmit={handleFormSubmit}
                isSubmitting={isSubmitting}
              />
            </div>

            {/* Additional Information */}
            <div className="mt-8 max-w-3xl mx-auto">
              <Card className="tron-card bg-card/30 backdrop-blur-sm border border-primary/20">
                <CardHeader>
                  <CardTitle className="text-lg text-foreground glow-cyan">What Gets Generated</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-foreground mb-2 glow-cyan">Work Items</h4>
                      <ul className="text-muted-foreground space-y-1">
                        <li>• Domain-specific Epics</li>
                        <li>• Industry-relevant Features</li>
                        <li>• Contextual User Stories</li>
                        <li>• Technical Implementation Tasks</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-foreground mb-2 glow-cyan">Quality Assurance</h4>
                      <ul className="text-muted-foreground space-y-1">
                        <li>• Comprehensive Test Plans</li>
                        <li>• Test Suites by Requirement</li>
                        <li>• Domain-aware Test Cases</li>
                        <li>• Industry-standard Test Data</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 rounded-lg border border-blue-500/30 bg-blue-500/10">
                    <div className="flex items-start space-x-2 text-blue-300 text-sm">
                      <FiInfo className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium mb-1">Domain Intelligence in Action:</p>
                        <p>
                          When you select "Healthcare" as your domain, the AI will generate user stories for doctors, nurses, and patients 
                          using medical terminology like "clinical workflow," "patient records," and "treatment plans." The same vision 
                          statement would produce different, more relevant results for "Oil & Gas" with terms like "field operations," 
                          "drilling efficiency," and "production optimization."
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewProjectScreen;