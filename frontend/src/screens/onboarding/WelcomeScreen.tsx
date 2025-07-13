import React from 'react';
import { Button } from '../../components/ui/button';
import { useNavigate } from 'react-router-dom';

const WelcomeScreen: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="container mx-auto flex-1">
        <div className="flex flex-col md:flex-row items-center justify-center min-h-screen py-10 gap-8">
          <div className="space-y-6 max-w-lg">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight">
              <span className="relative text-primary">
                Agile Backlog Automation
              </span>
              <br />
              <span className="text-accent-foreground">
                AI-Powered Project Planning
              </span>
            </h1>
            
            <p className="text-muted-foreground text-base lg:text-lg">
              Create comprehensive product backlogs in minutes instead of days.
              Our AI-powered system helps project managers, business analysts,
              and product owners create high-quality backlogs with minimal effort.
            </p>
            
            <div className="flex flex-col sm:flex-row space-y-6 sm:space-y-0 sm:space-x-6">
              <Button
                size="lg"
                className="px-6 font-bold"
                onClick={() => navigate('/project/new')}
              >
                Create New Project
              </Button>
              
              <Button
                size="lg"
                variant="outline"
                className="px-6 font-bold"
                onClick={() => navigate('/dashboard')}
              >
                View Dashboard
              </Button>
            </div>
          </div>
          
          <div className="rounded-2xl bg-card shadow-xl p-6 overflow-hidden min-w-full md:min-w-[400px] max-w-full md:max-w-[450px]">
            {/* Placeholder for an illustration or screenshot */}
            <div className="h-[300px] bg-muted rounded-lg flex items-center justify-center">
              {/* Replace with actual image */}
              <p className="p-4 text-center text-muted-foreground">Project Dashboard Preview</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
