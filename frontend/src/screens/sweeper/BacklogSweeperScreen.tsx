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
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  Badge,
  Divider,
  Progress,
  Icon,
  Checkbox,
  CheckboxGroup,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { 
  FiRefreshCw, 
  FiArrowLeft, 
  FiPlay, 
  FiSettings, 
  FiCheckCircle, 
  FiClock,
  FiUsers,
  FiTarget,
  FiTrendingUp
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface SweeperConfig {
  targetAreaPaths: string[];
  enhancementOptions: string[];
  qualityChecks: string[];
  agentMode: 'manual' | 'automatic';
}

const BacklogSweeperScreen: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState<SweeperConfig>({
    targetAreaPaths: ['Backlog Automation\\Grit', 'Backlog Automation\\Data Visualization'],
    enhancementOptions: ['acceptance_criteria', 'user_stories', 'task_decomposition'],
    qualityChecks: ['completeness', 'clarity', 'testability'],
    agentMode: 'automatic',
  });
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  const enhancementOptions = [
    { value: 'acceptance_criteria', label: 'Generate Acceptance Criteria', description: 'Auto-generate detailed acceptance criteria for user stories' },
    { value: 'user_stories', label: 'Decompose Epics to User Stories', description: 'Break down epics into manageable user stories' },
    { value: 'task_decomposition', label: 'Task Decomposition', description: 'Split user stories into development tasks' },
    { value: 'test_cases', label: 'Generate Test Cases', description: 'Create test cases based on acceptance criteria' },
    { value: 'estimates', label: 'Story Point Estimation', description: 'AI-assisted story point estimation' },
  ];

  const qualityCheckOptions = [
    { value: 'completeness', label: 'Completeness Check', description: 'Ensure all required fields are filled' },
    { value: 'clarity', label: 'Clarity Analysis', description: 'Check for clear and understandable descriptions' },
    { value: 'testability', label: 'Testability Review', description: 'Verify that requirements are testable' },
    { value: 'dependencies', label: 'Dependency Analysis', description: 'Identify and flag dependencies between items' },
    { value: 'priority_alignment', label: 'Priority Alignment', description: 'Check if priorities are consistently set' },
  ];

  const handleRunSweeper = async () => {
    setIsLoading(true);
    setProgress(0);
    setCurrentOperation('Initializing backlog sweeper...');

    try {
      await simulateSweeperRun();
      setIsComplete(true);
      toast({
        title: 'Backlog Sweeper Complete',
        description: 'Successfully enhanced backlog items with AI-powered improvements',
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Sweeper Failed',
        description: 'An error occurred during the backlog enhancement process',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const simulateSweeperRun = async () => {
    const steps = [
      { text: 'Connecting to Azure DevOps...', duration: 1000 },
      { text: 'Loading backlog items from target areas...', duration: 1500 },
      { text: 'Analyzing Epic structure and relationships...', duration: 1200 },
      { text: 'Generating acceptance criteria for user stories...', duration: 2000 },
      { text: 'Decomposing epics into user stories...', duration: 1800 },
      { text: 'Creating development tasks...', duration: 1500 },
      { text: 'Running quality checks...', duration: 1000 },
      { text: 'Applying AI-powered enhancements...', duration: 1200 },
      { text: 'Updating work items in Azure DevOps...', duration: 800 },
      { text: 'Backlog enhancement completed successfully', duration: 500 },
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentOperation(steps[i].text);
      setProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, steps[i].duration));
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
          <Heading size="lg" mb={2} color="green.500">
            <Icon as={FiRefreshCw} mr={3} />
            Backlog Sweeper
          </Heading>
          <Text color="gray.600">
            Automated backlog enhancement with AI-powered quality improvements
          </Text>
        </Box>

        {/* Info Alert */}
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Intelligent Backlog Enhancement</AlertTitle>
            <AlertDescription>
              The backlog sweeper uses AI agents to automatically improve your backlog items with 
              better acceptance criteria, task decomposition, and quality checks.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Configuration Tabs */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Sweeper Configuration</Heading>
          </CardHeader>
          <CardBody>
            <Tabs>
              <TabList>
                <Tab>Enhancement Options</Tab>
                <Tab>Quality Checks</Tab>
                <Tab>Agent Settings</Tab>
              </TabList>

              <TabPanels>
                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <Text fontSize="sm" color="gray.600" mb={2}>
                      Select which enhancements to apply to your backlog items:
                    </Text>
                    <CheckboxGroup
                      value={config.enhancementOptions}
                      onChange={(values) => setConfig(prev => ({ ...prev, enhancementOptions: values as string[] }))}
                    >
                      <VStack spacing={3} align="stretch">
                        {enhancementOptions.map((option) => (
                          <Checkbox key={option.value} value={option.value}>
                            <VStack align="start" spacing={0}>
                              <Text fontWeight="medium">{option.label}</Text>
                              <Text fontSize="sm" color="gray.600">{option.description}</Text>
                            </VStack>
                          </Checkbox>
                        ))}
                      </VStack>
                    </CheckboxGroup>
                  </VStack>
                </TabPanel>

                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <Text fontSize="sm" color="gray.600" mb={2}>
                      Select quality checks to perform on your backlog:
                    </Text>
                    <CheckboxGroup
                      value={config.qualityChecks}
                      onChange={(values) => setConfig(prev => ({ ...prev, qualityChecks: values as string[] }))}
                    >
                      <VStack spacing={3} align="stretch">
                        {qualityCheckOptions.map((option) => (
                          <Checkbox key={option.value} value={option.value}>
                            <VStack align="start" spacing={0}>
                              <Text fontWeight="medium">{option.label}</Text>
                              <Text fontSize="sm" color="gray.600">{option.description}</Text>
                            </VStack>
                          </Checkbox>
                        ))}
                      </VStack>
                    </CheckboxGroup>
                  </VStack>
                </TabPanel>

                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel>Agent Mode</FormLabel>
                      <Select
                        value={config.agentMode}
                        onChange={(e) => setConfig(prev => ({ ...prev, agentMode: e.target.value as 'manual' | 'automatic' }))}
                      >
                        <option value="automatic">Automatic - Full AI automation</option>
                        <option value="manual">Manual - Review each change</option>
                      </Select>
                    </FormControl>

                    <FormControl>
                      <FormLabel>Target Area Paths</FormLabel>
                      <Textarea
                        value={config.targetAreaPaths.join('\n')}
                        onChange={(e) => setConfig(prev => ({ 
                          ...prev, 
                          targetAreaPaths: e.target.value.split('\n').filter(path => path.trim()) 
                        }))}
                        placeholder="Enter area paths, one per line"
                        rows={3}
                      />
                    </FormControl>
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>

        {/* Available Agents */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Available AI Agents</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <HStack>
                <Icon as={FiUsers} color="blue.500" />
                <Text fontWeight="medium">Epic Strategist</Text>
                <Badge colorScheme="blue">ACTIVE</Badge>
              </HStack>
              <Text fontSize="sm" color="gray.600" ml={6}>
                Analyzes epic structure and breaks down large initiatives into manageable pieces
              </Text>

              <HStack>
                <Icon as={FiTarget} color="green.500" />
                <Text fontWeight="medium">User Story Decomposer</Text>
                <Badge colorScheme="green">ACTIVE</Badge>
              </HStack>
              <Text fontSize="sm" color="gray.600" ml={6}>
                Creates detailed user stories with acceptance criteria and task breakdowns
              </Text>

              <HStack>
                <Icon as={FiTrendingUp} color="purple.500" />
                <Text fontWeight="medium">QA Lead Agent</Text>
                <Badge colorScheme="purple">ACTIVE</Badge>
              </HStack>
              <Text fontSize="sm" color="gray.600" ml={6}>
                Performs quality checks and ensures testability of all backlog items
              </Text>
            </VStack>
          </CardBody>
        </Card>

        {/* Action Buttons */}
        <HStack spacing={4}>
          <Button
            leftIcon={<Icon as={FiPlay} />}
            colorScheme="green"
            size="lg"
            onClick={handleRunSweeper}
            isLoading={isLoading}
            loadingText={currentOperation}
          >
            Run Backlog Sweeper
          </Button>
          <Button
            leftIcon={<Icon as={FiSettings} />}
            variant="outline"
            size="lg"
            onClick={() => navigate('/settings')}
            isDisabled={isLoading}
          >
            Advanced Settings
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate('/dashboard')}
            isDisabled={isLoading}
          >
            Cancel
          </Button>
        </HStack>

        {/* Progress Section */}
        {(isLoading || isComplete) && (
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">
                {isLoading ? 'Backlog Enhancement in Progress' : 'Enhancement Complete'}
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                {isLoading && (
                  <>
                    <Progress value={progress} colorScheme="green" size="lg" borderRadius="md" />
                    <Text fontSize="sm" color="gray.600">{currentOperation}</Text>
                  </>
                )}
                
                {isComplete && (
                  <>
                    <Divider />
                    <Text fontWeight="bold" color="green.600">
                      Backlog enhancement completed successfully!
                    </Text>
                    <List spacing={2}>
                      <ListItem>
                        <ListIcon as={FiCheckCircle} color="green.500" />
                        Generated acceptance criteria for 45 user stories
                      </ListItem>
                      <ListItem>
                        <ListIcon as={FiCheckCircle} color="green.500" />
                        Decomposed 8 epics into 32 new user stories
                      </ListItem>
                      <ListItem>
                        <ListIcon as={FiCheckCircle} color="green.500" />
                        Created 127 development tasks
                      </ListItem>
                      <ListItem>
                        <ListIcon as={FiCheckCircle} color="green.500" />
                        Performed quality checks on all items
                      </ListItem>
                    </List>
                  </>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default BacklogSweeperScreen;
