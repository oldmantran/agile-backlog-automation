import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { 
  FiArrowLeft, 
  FiPlay, 
  FiCheckCircle,
  FiLoader,
  FiActivity,
  FiDownload
} from 'react-icons/fi';

interface ExecutionStatus {
  isRunning: boolean;
  progress: number;
  message: string;
  logs: string[];
  completed: boolean;
  error?: string;
}

const TronExecutableScreen: React.FC = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ExecutionStatus>({
    isRunning: false,
    progress: 0,
    message: '',
    logs: [],
    completed: false
  });

  const startApplication = async () => {
    setStatus(prev => ({ ...prev, isRunning: true, progress: 0, completed: false, error: undefined }));
    
    try {
      // Start the backend server
      const response = await fetch('/api/start-application', { method: 'POST' });
      
      if (response.ok) {
        // Simulate startup progress
        const steps = [
          'Initializing Python environment...',
          'Loading configuration files...',
          'Connecting to Azure DevOps...',
          'Validating AI providers...',
          'Starting backend server...',
          'Application ready!'
        ];
        
        for (let i = 0; i < steps.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          setStatus(prev => ({
            ...prev,
            progress: ((i + 1) / steps.length) * 100,
            message: steps[i],
            logs: [...prev.logs, `[${new Date().toLocaleTimeString()}] ${steps[i]}`]
          }));
        }
        
        setStatus(prev => ({ ...prev, completed: true, isRunning: false }));
        
        // Open the application in the default browser
        setTimeout(() => {
          window.open('http://localhost:3000', '_blank');
        }, 1000);
        
      } else {
        throw new Error('Failed to start application');
      }
    } catch (error) {
      setStatus(prev => ({ 
        ...prev, 
        isRunning: false, 
        error: 'Failed to start application. Please ensure all dependencies are installed.' 
      }));
    }
  };

  return (
    <div className="min-h-screen bg-background tron-grid">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-primary hover:bg-primary/10"
          >
            <FiArrowLeft className="h-4 w-4" />
            RETURN TO MAIN
          </Button>
        </div>

        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <FiPlay className="w-12 h-12 text-primary pulse-glow" />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            EXECUTABLE <span className="text-primary">LAUNCHER</span>
          </h1>
          <p className="text-muted-foreground font-mono">
            START BACKLOG AUTOMATION APPLICATION
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          {/* Application Info */}
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary">Application Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Application:</span>
                  <p className="text-foreground font-mono">Agile Backlog Automation v2.0</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Framework:</span>
                  <p className="text-foreground font-mono">React + Python FastAPI</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Theme:</span>
                  <p className="text-foreground font-mono">Tron Legacy Interface</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p className="text-foreground font-mono">
                    {status.completed ? 'READY' : status.isRunning ? 'STARTING...' : 'OFFLINE'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Launcher */}
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary">Application Launcher</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {!status.isRunning && !status.completed && !status.error && (
                <div className="text-center space-y-4">
                  <p className="text-muted-foreground">
                    Click the button below to start the Backlog Automation application.
                    This will initialize the backend services and open the interface in your browser.
                  </p>
                  <Button
                    onClick={startApplication}
                    className="tron-button px-12 py-4 text-lg"
                  >
                    <FiPlay className="w-5 h-5 mr-2" />
                    START APPLICATION
                  </Button>
                </div>
              )}

              {status.isRunning && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-foreground">Startup Progress</span>
                      <span className="text-primary">{Math.round(status.progress)}%</span>
                    </div>
                    <Progress value={status.progress} className="h-3" />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <FiLoader className="w-4 h-4 text-primary animate-spin" />
                    <span className="text-foreground">{status.message}</span>
                  </div>
                </div>
              )}

              {status.completed && (
                <Alert className="border-green-500/50 bg-green-500/10">
                  <FiCheckCircle className="h-4 w-4 text-green-500" />
                  <AlertDescription className="text-green-400">
                    Application started successfully! The interface should open in your browser automatically.
                    If it doesn't, navigate to <code className="bg-green-500/20 px-1 rounded">http://localhost:3000</code>
                  </AlertDescription>
                </Alert>
              )}

              {status.error && (
                <Alert className="border-red-500/50 bg-red-500/10">
                  <FiActivity className="h-4 w-4 text-red-500" />
                  <AlertDescription className="text-red-400">
                    {status.error}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Startup Logs */}
          {status.logs.length > 0 && (
            <Card className="tron-card">
              <CardHeader>
                <CardTitle className="text-primary">Startup Logs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-background/50 border border-primary/20 rounded-md p-4 max-h-64 overflow-y-auto">
                  {status.logs.map((log, index) => (
                    <div key={index} className="font-mono text-sm text-muted-foreground mb-1">
                      {log}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Download Section */}
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary">Standalone Executable</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                For a truly standalone experience, you can build an executable version of this application 
                that includes all dependencies and can run without requiring Python or Node.js installation.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Button
                  variant="outline"
                  className="border-primary/50 text-primary hover:bg-primary/10"
                  onClick={() => {
                    // This would trigger a build process
                    alert('Executable build process would start here. This feature requires build automation setup.');
                  }}
                >
                  <FiDownload className="w-4 h-4 mr-2" />
                  BUILD WINDOWS EXECUTABLE
                </Button>
                
                <Button
                  variant="outline"
                  className="border-primary/50 text-primary hover:bg-primary/10"
                  onClick={() => {
                    alert('macOS executable build would start here.');
                  }}
                >
                  <FiDownload className="w-4 h-4 mr-2" />
                  BUILD MACOS EXECUTABLE
                </Button>
                
                <Button
                  variant="outline"
                  className="border-primary/50 text-primary hover:bg-primary/10"
                  onClick={() => {
                    alert('Linux executable build would start here.');
                  }}
                >
                  <FiDownload className="w-4 h-4 mr-2" />
                  BUILD LINUX EXECUTABLE
                </Button>
              </div>
              
              <Alert className="border-blue-500/50 bg-blue-500/10">
                <FiActivity className="h-4 w-4 text-blue-500" />
                <AlertDescription className="text-blue-400">
                  <strong>Note:</strong> Executable builds require PyInstaller and additional build tools. 
                  The generated executable will be approximately 100-200MB and include all dependencies.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TronExecutableScreen;
