import React, { useState } from 'react';
import {
  Box,
  VStack,
  Text,
  Progress,
  useToast,
  Container,
  Stepper,
  Step,
  StepIndicator,
  StepStatus,
  StepIcon,
  StepNumber,
  StepTitle,
  StepDescription,
  StepSeparator,
  useSteps,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';

import ProjectBasicsForm from '../../components/forms/ProjectBasicsForm';
import VisionForm from '../../components/forms/VisionForm';
import AzureSetupForm from '../../components/forms/AzureSetupForm';
import AiConfigForm from '../../components/forms/AiConfigForm';
import ReviewForm from '../../components/forms/ReviewForm';

const MotionBox = motion(Box);

const steps = [
  { title: 'Project Basics', description: 'Name, domain, and size', component: ProjectBasicsForm },
  { title: 'Vision', description: 'Goals and objectives', component: VisionForm },
  { title: 'Azure Setup', description: 'Connect to Azure DevOps', component: AzureSetupForm },
  { title: 'AI Configuration', description: 'Configure generation options', component: AiConfigForm },
  { title: 'Review', description: 'Review and generate', component: ReviewForm },
];

const ProjectWizard: React.FC = () => {
  const toast = useToast();
  const [projectData, setProjectData] = useState({});
  const { activeStep, setActiveStep } = useSteps({
    index: 0,
    count: steps.length,
  });

  const CurrentStepComponent = steps[activeStep].component;

  const handleNext = (stepData: any) => {
    setProjectData(prev => ({ ...prev, ...stepData }));
    
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
    } else {
      // Final step - show success
      toast({
        title: 'Project Created!',
        description: 'Your backlog generation has started.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handlePrevious = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };

  return (
    <Container maxW="container.md" py={8}>
      <VStack spacing={8} w="full">
        {/* Header */}
        <VStack spacing={4} w="full">
          <Text fontSize="3xl" fontWeight="bold" color="brand.500" textAlign="center">
            Create New Project
          </Text>
          
          <Stepper index={activeStep} colorScheme="brand" size="sm" mb={8}>
            {steps.map((step, index) => (
              <Step key={index}>
                <StepIndicator>
                  <StepStatus
                    complete={<StepIcon />}
                    incomplete={<StepNumber />}
                    active={<StepNumber />}
                  />
                </StepIndicator>
                <Box flexShrink={0}>
                  <StepTitle>{step.title}</StepTitle>
                  <StepDescription>{step.description}</StepDescription>
                </Box>
                <StepSeparator />
              </Step>
            ))}
          </Stepper>
        </VStack>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <MotionBox
            key={activeStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            w="full"
          >
            <CurrentStepComponent
              onNext={handleNext}
              onPrevious={activeStep > 0 ? handlePrevious : undefined}
              initialData={projectData}
            />
          </MotionBox>
        </AnimatePresence>
      </VStack>
    </Container>
  );
};

export default ProjectWizard;
