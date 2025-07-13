import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  useToast,
  Badge,
  Divider,
  Progress,
  Icon,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  SimpleGrid,
  List,
  ListItem,
  ListIcon,
  useColorModeValue,
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
  CheckboxGroup,
  Checkbox,
  Stack,
} from '@chakra-ui/react';
import { 
  FiPlus, 
  FiArrowLeft, 
  FiCheckCircle, 
  FiSettings,
  FiUsers,
  FiTarget,
  FiCode,
  FiDatabase,
  FiCloud,
  FiGitBranch,
  FiFolder,
  FiArrowRight
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface ProjectConfig {
  name: string;
  description: string;
  organization: string;
  teamProject: string;
  areaPath: string;
  iterationPath: string;
  projectType: string;
  features: string[];
  agents: string[];
}

const steps = [
  { title: 'Project Details', description: 'Basic project information' },
  { title: 'Azure DevOps', description: 'Configure ADO integration' },
  { title: 'Features & Agents', description: 'Select automation features' },
  { title: 'Confirmation', description: 'Review and create project' },
];

const NewProjectScreen: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const { activeStep, setActiveStep } = useSteps({
    index: 0,
    count: steps.length,
  });

  const [isCreating, setIsCreating] = useState(false);
  const [config, setConfig] = useState<ProjectConfig>({
    name: '',
    description: '',
    organization: '',
    teamProject: '',
    areaPath: '',
    iterationPath: '',
    projectType: 'agile',
    features: ['backlog_enhancement', 'quality_checks'],
    agents: ['epic_strategist', 'user_story_decomposer'],
  });
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');

  const projectTypes = [
    { value: 'agile', label: 'Agile Development', description: 'Standard agile project with sprints and user stories' },
    { value: 'scrum', label: 'Scrum Framework', description: 'Scrum-based project with defined roles and ceremonies' },
    { value: 'kanban', label: 'Kanban Board', description: 'Continuous flow project with WIP limits' },
    { value: 'hybrid', label: 'Hybrid Approach', description: 'Custom mix of agile methodologies' },
  ];

  const availableFeatures = [
    { value: 'backlog_enhancement', label: 'Backlog Enhancement', description: 'Automated backlog item improvement' },
    { value: 'quality_checks', label: 'Quality Assurance', description: 'Automated quality checks and validation' },
    { value: 'test_automation', label: 'Test Case Generation', description: 'AI-powered test case creation' },
    { value: 'story_estimation', label: 'Story Point Estimation', description: 'Automated story point estimation' },
    { value: 'dependency_analysis', label: 'Dependency Analysis', description: 'Automatic dependency detection' },
    { value: 'sprint_planning', label: 'Sprint Planning', description: 'AI-assisted sprint planning' },
  ];

  const availableAgents = [
    { value: 'epic_strategist', label: 'Epic Strategist', description: 'Breaks down large initiatives', icon: FiTarget },
    { value: 'user_story_decomposer', label: 'User Story Decomposer', description: 'Creates detailed user stories', icon: FiUsers },
    { value: 'qa_lead_agent', label: 'QA Lead Agent', description: 'Quality assurance and testing', icon: FiCheckCircle },
    { value: 'developer_agent', label: 'Developer Agent', description: 'Technical task management', icon: FiCode },
    { value: 'feature_decomposer', label: 'Feature Decomposer', description: 'Feature breakdown and planning', icon: FiFolder },
  ];

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
    }
  };

  const handlePrevious = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };

  const handleCreateProject = async () => {
    setIsCreating(true);
    setProgress(0);
    setCurrentOperation('Initializing project creation...');

    try {
      await simulateProjectCreation();
      toast({
        title: 'Project Created Successfully',
        description: `${config.name} has been set up with all selected features`,
        status: 'success',
        duration: 5000,
      });
      navigate('/dashboard');
    } catch (error) {
      toast({
        title: 'Project Creation Failed',
        description: 'An error occurred while creating the project',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsCreating(false);
    }
  };

  const simulateProjectCreation = async () => {
    const operations = [
      { text: 'Validating Azure DevOps connection...', duration: 1000 },
      { text: 'Creating project structure...', duration: 1500 },
      { text: 'Setting up area paths and iterations...', duration: 1200 },
      { text: 'Configuring AI agents...', duration: 1800 },
      { text: 'Initializing backlog automation features...', duration: 1500 },
      { text: 'Setting up quality checks...', duration: 1000 },
      { text: 'Creating initial project dashboard...', duration: 800 },
      { text: 'Project setup completed successfully', duration: 500 },
    ];

    for (let i = 0; i < operations.length; i++) {
      setCurrentOperation(operations[i].text);
      setProgress((i + 1) / operations.length * 100);
      await new Promise(resolve => setTimeout(resolve, operations[i].duration));
    }
  };

  const isStepValid = () => {
    switch (activeStep) {
      case 0:
        return config.name.trim() && config.description.trim();
      case 1:
        return config.organization.trim() && config.teamProject.trim();
      case 2:
        return config.features.length > 0 && config.agents.length > 0;
      default:
        return true;
    }
  };

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack>
          <Button
            leftIcon={<Icon as={FiArrowLeft} />}
            variant="ghost"
            onClick={() => navigate('/dashboard')}
          >
            Back to Dashboard
          </Button>
        </HStack>

        <Box>
          <Heading size="lg" mb={2} color="blue.500">
            <Icon as={FiPlus} mr={3} />
            Create New Project
          </Heading>
          <Text color="gray.600">
            Set up a new agile project with AI-powered automation
          </Text>
        </Box>

        {/* Progress Stepper */}
        <Card bg={cardBg}>
          <CardBody>
            <Stepper index={activeStep}>
              {steps.map((step, index) => (
                <Step key={index}>
                  <StepIndicator>
                    <StepStatus
                      complete={<StepIcon />}
                      incomplete={<StepNumber />}
                      active={<StepNumber />}
                    />
                  </StepIndicator>

                  <Box flexShrink="0">
                    <StepTitle>{step.title}</StepTitle>
                    <StepDescription>{step.description}</StepDescription>
                  </Box>

                  <StepSeparator />
                </Step>
              ))}
            </Stepper>
          </CardBody>
        </Card>

        {/* Step Content */}
        <Card bg={cardBg} minH="400px">
          <CardBody>
            {activeStep === 0 && (
              <VStack spacing={6} align="stretch">
                <Heading size="md">Project Details</Heading>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                  <FormControl isRequired>
                    <FormLabel>Project Name</FormLabel>
                    <Input
                      placeholder="e.g., Customer Portal Enhancement"
                      value={config.name}
                      onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Project Type</FormLabel>
                    <Select
                      value={config.projectType}
                      onChange={(e) => setConfig(prev => ({ ...prev, projectType: e.target.value }))}
                    >
                      {projectTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                </SimpleGrid>

                <FormControl isRequired>
                  <FormLabel>Project Description</FormLabel>
                  <Textarea
                    placeholder="Describe the goals and scope of your project..."
                    value={config.description}
                    onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                  />
                </FormControl>

                {config.projectType && (
                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>{projectTypes.find(t => t.value === config.projectType)?.label}</AlertTitle>
                      <AlertDescription>
                        {projectTypes.find(t => t.value === config.projectType)?.description}
                      </AlertDescription>
                    </Box>
                  </Alert>
                )}
              </VStack>
            )}

            {activeStep === 1 && (
              <VStack spacing={6} align="stretch">
                <Heading size="md">Azure DevOps Configuration</Heading>
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  <Box>
                    <AlertTitle>Azure DevOps Integration</AlertTitle>
                    <AlertDescription>
                      Ensure you have proper permissions to create work items in the target project.
                    </AlertDescription>
                  </Box>
                </Alert>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                  <FormControl isRequired>
                    <FormLabel>Organization</FormLabel>
                    <Input
                      placeholder="e.g., mycompany"
                      value={config.organization}
                      onChange={(e) => setConfig(prev => ({ ...prev, organization: e.target.value }))}
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Team Project</FormLabel>
                    <Input
                      placeholder="e.g., MyTeamProject"
                      value={config.teamProject}
                      onChange={(e) => setConfig(prev => ({ ...prev, teamProject: e.target.value }))}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Area Path</FormLabel>
                    <Input
                      placeholder="e.g., MyTeamProject\\MyFeature"
                      value={config.areaPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, areaPath: e.target.value }))}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Iteration Path</FormLabel>
                    <Input
                      placeholder="e.g., MyTeamProject\\Sprint 1"
                      value={config.iterationPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, iterationPath: e.target.value }))}
                    />
                  </FormControl>
                </SimpleGrid>
              </VStack>
            )}

            {activeStep === 2 && (
              <VStack spacing={6} align="stretch">
                <Heading size="md">Features & AI Agents</Heading>
                
                <Box>
                  <Text fontWeight="medium" mb={3}>Select Automation Features:</Text>
                  <CheckboxGroup
                    value={config.features}
                    onChange={(values) => setConfig(prev => ({ ...prev, features: values as string[] }))}
                  >
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                      {availableFeatures.map((feature) => (
                        <Checkbox key={feature.value} value={feature.value}>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="medium">{feature.label}</Text>
                            <Text fontSize="sm" color="gray.600">{feature.description}</Text>
                          </VStack>
                        </Checkbox>
                      ))}
                    </SimpleGrid>
                  </CheckboxGroup>
                </Box>

                <Divider />

                <Box>
                  <Text fontWeight="medium" mb={3}>Select AI Agents:</Text>
                  <CheckboxGroup
                    value={config.agents}
                    onChange={(values) => setConfig(prev => ({ ...prev, agents: values as string[] }))}
                  >
                    <VStack spacing={3} align="stretch">
                      {availableAgents.map((agent) => (
                        <Checkbox key={agent.value} value={agent.value}>
                          <HStack>
                            <Icon as={agent.icon} color="blue.500" />
                            <VStack align="start" spacing={0}>
                              <Text fontWeight="medium">{agent.label}</Text>
                              <Text fontSize="sm" color="gray.600">{agent.description}</Text>
                            </VStack>
                          </HStack>
                        </Checkbox>
                      ))}
                    </VStack>
                  </CheckboxGroup>
                </Box>
              </VStack>
            )}

            {activeStep === 3 && (
              <VStack spacing={6} align="stretch">
                <Heading size="md">Review & Create Project</Heading>
                
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                  <Card variant="outline">
                    <CardHeader>
                      <Heading size="sm">Project Information</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack spacing={3} align="stretch">
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">Name:</Text>
                          <Text fontSize="sm">{config.name}</Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">Type:</Text>
                          <Badge>{projectTypes.find(t => t.value === config.projectType)?.label}</Badge>
                        </HStack>
                        <Box>
                          <Text fontSize="sm" fontWeight="medium" mb={1}>Description:</Text>
                          <Text fontSize="sm" color="gray.600">{config.description}</Text>
                        </Box>
                      </VStack>
                    </CardBody>
                  </Card>

                  <Card variant="outline">
                    <CardHeader>
                      <Heading size="sm">Azure DevOps</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack spacing={3} align="stretch">
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">Organization:</Text>
                          <Text fontSize="sm">{config.organization}</Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">Project:</Text>
                          <Text fontSize="sm">{config.teamProject}</Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">Area Path:</Text>
                          <Text fontSize="sm">{config.areaPath || 'Root'}</Text>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>

                  <Card variant="outline">
                    <CardHeader>
                      <Heading size="sm">Selected Features</Heading>
                    </CardHeader>
                    <CardBody>
                      <Stack spacing={2}>
                        {config.features.map((featureValue) => {
                          const feature = availableFeatures.find(f => f.value === featureValue);
                          return (
                            <HStack key={featureValue}>
                              <Icon as={FiCheckCircle} color="green.500" size="12px" />
                              <Text fontSize="sm">{feature?.label}</Text>
                            </HStack>
                          );
                        })}
                      </Stack>
                    </CardBody>
                  </Card>

                  <Card variant="outline">
                    <CardHeader>
                      <Heading size="sm">AI Agents</Heading>
                    </CardHeader>
                    <CardBody>
                      <Stack spacing={2}>
                        {config.agents.map((agentValue) => {
                          const agent = availableAgents.find(a => a.value === agentValue);
                          return (
                            <HStack key={agentValue}>
                              <Icon as={agent?.icon || FiUsers} color="blue.500" size="12px" />
                              <Text fontSize="sm">{agent?.label}</Text>
                            </HStack>
                          );
                        })}
                      </Stack>
                    </CardBody>
                  </Card>
                </SimpleGrid>

                {isCreating && (
                  <Card bg="blue.50" borderColor="blue.200">
                    <CardBody>
                      <VStack spacing={4} align="stretch">
                        <Text fontWeight="bold" color="blue.700">Creating Project...</Text>
                        <Progress value={progress} colorScheme="blue" size="lg" borderRadius="md" />
                        <Text fontSize="sm" color="blue.600">{currentOperation}</Text>
                      </VStack>
                    </CardBody>
                  </Card>
                )}
              </VStack>
            )}
          </CardBody>
        </Card>

        {/* Navigation Buttons */}
        <HStack justify="space-between">
          <Button
            onClick={handlePrevious}
            isDisabled={activeStep === 0 || isCreating}
            variant="outline"
          >
            Previous
          </Button>

          <HStack>
            {activeStep < steps.length - 1 ? (
              <Button
                rightIcon={<Icon as={FiArrowRight} />}
                colorScheme="blue"
                onClick={handleNext}
                isDisabled={!isStepValid() || isCreating}
              >
                Next
              </Button>
            ) : (
              <Button
                leftIcon={<Icon as={FiPlus} />}
                colorScheme="green"
                onClick={handleCreateProject}
                isLoading={isCreating}
                loadingText="Creating Project..."
                isDisabled={!isStepValid()}
                size="lg"
              >
                Create Project
              </Button>
            )}
          </HStack>
        </HStack>
      </VStack>
    </Box>
  );
};

export default NewProjectScreen;
