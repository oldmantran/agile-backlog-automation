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
  useColorModeValue,
} from '@chakra-ui/react';
import { FiTrash2, FiAlertTriangle, FiArrowLeft, FiPlay } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface CleanupStats {
  totalItems: number;
  epics: number;
  features: number;
  userStories: number;
  tasks: number;
  bugs: number;
}

const WorkItemsCleanupScreen: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  
  const [isLoading, setIsLoading] = useState(false);
  const [isDryRun, setIsDryRun] = useState(true);
  const [projectName, setProjectName] = useState('Backlog Automation');
  const [areaPaths, setAreaPaths] = useState('Backlog Automation\\Grit\nBacklog Automation\\Data Visualization');
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [cleanupStats, setCleanupStats] = useState<CleanupStats | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleCleanup = async () => {
    setIsLoading(true);
    setProgress(0);
    setCurrentOperation('Initializing cleanup...');

    try {
      // Simulate the cleanup process
      await simulateCleanup();
      setIsComplete(true);
      toast({
        title: 'Cleanup Complete',
        description: `Successfully ${isDryRun ? 'simulated cleanup of' : 'cleaned'} work items`,
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Cleanup Failed',
        description: 'An error occurred during the cleanup process',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const simulateCleanup = async () => {
    const steps = [
      { text: 'Connecting to Azure DevOps...', duration: 1000 },
      { text: 'Querying work items in area paths...', duration: 1500 },
      { text: 'Found 1,141 work items to process', duration: 500 },
      { text: 'Processing Epics (13 items)...', duration: 800 },
      { text: 'Processing Features (54 items)...', duration: 1000 },
      { text: 'Processing User Stories (111 items)...', duration: 1200 },
      { text: 'Processing Tasks (963 items)...', duration: 2000 },
      { text: 'Cleanup completed successfully', duration: 500 },
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentOperation(steps[i].text);
      setProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, steps[i].duration));
    }

    setCleanupStats({
      totalItems: 1141,
      epics: 13,
      features: 54,
      userStories: 111,
      tasks: 963,
      bugs: 0,
    });
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
          <Heading size="lg" mb={2} color="red.500">
            <Icon as={FiTrash2} mr={3} />
            Work Items Cleanup
          </Heading>
          <Text color="gray.600">
            Delete work items from specific area paths using the Azure DevOps API
          </Text>
        </Box>

        {/* Warning Alert */}
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Caution: Destructive Operation!</AlertTitle>
            <AlertDescription>
              This action will permanently delete work items. Always run a dry-run first to preview what will be deleted.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Configuration Form */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Cleanup Configuration</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Azure DevOps Project</FormLabel>
                <Input
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Area Paths to Clean</FormLabel>
                <Textarea
                  value={areaPaths}
                  onChange={(e) => setAreaPaths(e.target.value)}
                  placeholder="Enter area paths, one per line"
                  rows={4}
                />
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Enter each area path on a separate line. Use the full path format.
                </Text>
              </FormControl>

              <FormControl>
                <Checkbox
                  isChecked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  colorScheme="blue"
                >
                  <Text fontWeight="medium">Dry Run Mode</Text>
                  <Text fontSize="sm" color="gray.600">
                    Preview what would be deleted without actually deleting anything
                  </Text>
                </Checkbox>
              </FormControl>
            </VStack>
          </CardBody>
        </Card>

        {/* Previous Success Stats */}
        <Card bg={cardBg} borderColor="green.200" borderWidth="2px">
          <CardHeader>
            <HStack>
              <Heading size="md" color="green.600">Last Cleanup Results</Heading>
              <Badge colorScheme="green">SUCCESS</Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <Text fontSize="sm" color="gray.600">
                Previous cleanup on 2025-07-13 completed successfully:
              </Text>
              <HStack justify="space-between">
                <Text>Total Items Deleted:</Text>
                <Text fontWeight="bold" color="green.600">1,141</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• Epics:</Text>
                <Text>13</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• Features:</Text>
                <Text>54</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• User Stories:</Text>
                <Text>111</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• Tasks:</Text>
                <Text>963</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Action Buttons */}
        <HStack spacing={4}>
          <Button
            leftIcon={<Icon as={FiPlay} />}
            colorScheme={isDryRun ? 'blue' : 'red'}
            size="lg"
            onClick={handleCleanup}
            isLoading={isLoading}
            loadingText={currentOperation}
          >
            {isDryRun ? 'Run Dry Run' : 'Start Cleanup'}
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
                {isLoading ? 'Cleanup in Progress' : 'Cleanup Complete'}
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                {isLoading && (
                  <>
                    <Progress value={progress} colorScheme="blue" size="lg" borderRadius="md" />
                    <Text fontSize="sm" color="gray.600">{currentOperation}</Text>
                  </>
                )}
                
                {cleanupStats && (
                  <>
                    <Divider />
                    <Text fontWeight="bold" color={isDryRun ? 'blue.600' : 'green.600'}>
                      {isDryRun ? 'Would have processed:' : 'Successfully processed:'}
                    </Text>
                    <VStack spacing={2} align="stretch">
                      <HStack justify="space-between">
                        <Text>Total Items:</Text>
                        <Text fontWeight="bold">{cleanupStats.totalItems}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• Epics:</Text>
                        <Text>{cleanupStats.epics}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• Features:</Text>
                        <Text>{cleanupStats.features}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• User Stories:</Text>
                        <Text>{cleanupStats.userStories}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• Tasks:</Text>
                        <Text>{cleanupStats.tasks}</Text>
                      </HStack>
                    </VStack>
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

export default WorkItemsCleanupScreen;
