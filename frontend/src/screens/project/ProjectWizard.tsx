import React, { useState } from 'react';
import WizardLayout from '../../components/layout/WizardLayout';
import ProjectBasicsForm from '../../components/forms/ProjectBasicsForm';
import AzureSetupForm from '../../components/forms/AzureSetupForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';

interface ProjectData {
  basics?: any;
  azure?: any;
  ai?: any;
}

const ProjectWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [projectData, setProjectData] = useState<ProjectData>({});

  const steps = [
    'Project Basics',
    'Azure DevOps Setup',
    'AI Configuration',
    'Review & Create'
  ];

  const handleStepData = (stepKey: string, data: any) => {
    setProjectData(prev => ({
      ...prev,
      [stepKey]: data
    }));
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const previousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <ProjectBasicsForm
            onNext={(data) => {
              handleStepData('basics', data);
              nextStep();
            }}
            initialData={projectData.basics}
          />
        );
      case 1:
        return (
          <AzureSetupForm
            onNext={(data) => {
              handleStepData('azure', data);
              nextStep();
            }}
            onPrevious={previousStep}
            initialData={projectData.azure}
          />
        );
      case 2:
        return (
          <Card className="w-full max-w-2xl mx-auto shadow-lg border-cyan-500/20">
            <CardHeader>
              <CardTitle className="text-cyan-100">AI Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-cyan-400">AI Configuration form coming soon...</p>
            </CardContent>
          </Card>
        );
      case 3:
        return (
          <Card className="w-full max-w-2xl mx-auto shadow-lg border-cyan-500/20">
            <CardHeader>
              <CardTitle className="text-cyan-100">Review & Create</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-cyan-400">Project review coming soon...</p>
            </CardContent>
          </Card>
        );
      default:
        return null;
    }
  };

  return (
    <WizardLayout
      title="Create New Project"
      steps={steps}
      currentStep={currentStep}
    >
      {renderStepContent()}
    </WizardLayout>
  );
};

export default ProjectWizard;
