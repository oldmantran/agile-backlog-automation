import React, { useState } from 'react';
import {
  Box,
  VStack,
  Heading,
  Progress,
  useToast,
  Container,
} from '@chakra-ui/react';
import WizardLayout from '../../components/layout/WizardLayout';
import ProjectBasicsForm from '../../components/forms/ProjectBasicsForm';
import AzureSetupForm from '../../components/forms/AzureSetupForm';
import AiConfigForm from '../../components/forms/AiConfigForm';
import ReviewForm from '../../components/forms/ReviewForm';
import { Project, ProjectBasics, AzureConfig } from '../../types/project';

const ProjectWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [projectData, setProjectData] = useState<Partial<Project>>({});
  const toast = useToast();

  const totalSteps = 4;
  const progress = (currentStep / totalSteps) * 100;

  const handleNext = (stepData: any) => {
    setProjectData((prev: Partial<Project>) => ({ ...prev, ...stepData }));
    
    if (currentStep < totalSteps) {
      setCurrentStep(prev => prev + 1);
    } else {
      // Final submission
      handleSubmit({ ...projectData, ...stepData });
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async (finalData: Partial<Project>) => {
    try {
      // TODO: Implement API call to create project
      console.log('Submitting project data:', finalData);
      
      toast({
        title: 'Project Created',
        description: 'Your project has been successfully created!',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      // Navigate to dashboard or project view
      // TODO: Implement navigation
      
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create project. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getStepTitle = () => {
    switch (currentStep) {
      case 1: return 'Project Basics';
      case 2: return 'Azure DevOps Setup';
      case 3: return 'AI Configuration';
      case 4: return 'Review & Create';
      default: return 'Project Setup';
    }
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <ProjectBasicsForm
            initialData={projectData}
            onNext={handleNext}
            onPrevious={currentStep > 1 ? handleBack : undefined}
          />
        );
      case 2:
        return (
          <AzureSetupForm
            initialData={projectData}
            onNext={handleNext}
            onPrevious={handleBack}
          />
        );
      case 3:
        return (
          <AiConfigForm
            initialData={projectData}
            onNext={handleNext}
            onPrevious={handleBack}
          />
        );
      case 4:
        return (
          <ReviewForm
            initialData={projectData}
            onSubmit={handleNext}
            onPrevious={handleBack}
          />
        );
      default:
        return null;
    }
  };

  return (
    <WizardLayout>
      <Container maxW="container.md" py={8}>
        <VStack spacing={8} align="stretch">
          <Box textAlign="center">
            <Heading size="lg" mb={4}>
              {getStepTitle()}
            </Heading>
            <Box mb={6}>
              <Progress
                value={progress}
                colorScheme="blue"
                size="lg"
                borderRadius="md"
                bg="gray.100"
              />
              <Box
                mt={2}
                fontSize="sm"
                color="gray.600"
                textAlign="center"
              >
                Step {currentStep} of {totalSteps}
              </Box>
            </Box>
          </Box>

          <Box
            bg="white"
            p={8}
            borderRadius="lg"
            boxShadow="sm"
            border="1px"
            borderColor="gray.200"
          >
            {renderCurrentStep()}
          </Box>
        </VStack>
      </Container>
    </WizardLayout>
  );
};

export default ProjectWizard;
