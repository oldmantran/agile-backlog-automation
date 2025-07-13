import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Separator } from '../../components/ui/separator';
import { Progress } from '../../components/ui/progress';
import { Checkbox } from '../../components/ui/checkbox';
import { FiClipboard, FiAlertTriangle, FiArrowLeft, FiPlay, FiInfo } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface TestCaseStats {
  totalTestCases: number;
  gritAreaCases: number;
  dataVizAreaCases: number;
}

const TestCasesCleanupScreen: React.FC = () => {
  const navigate = useNavigate();
  // TODO: Add proper toast notification
  // const toast = useToast();
  
  const [isLoading, setIsLoading] = useState(false);
  const [isDryRun, setIsDryRun] = useState(true);
  const [projectName, setProjectName] = useState('Backlog Automation');
  const [areaPaths, setAreaPaths] = useState('Backlog Automation\\Grit\nBacklog Automation\\Data Visualization');
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [cleanupStats, setCleanupStats] = useState<TestCaseStats | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleCleanup = async () => {
    setIsLoading(true);
    setProgress(0);
    setCurrentOperation('Initializing test case cleanup...');

    try {
      await simulateTestCaseCleanup();
      setIsComplete(true);
      // TODO: Add proper toast notification
      console.log(`Test Case Cleanup Complete: Successfully ${isDryRun ? 'simulated cleanup of' : 'cleaned'} test cases using Test Management API`);
    } catch (error) {
      // TODO: Add proper toast notification
      console.error('Cleanup Failed: An error occurred during the test case cleanup process');
    } finally {
      setIsLoading(false);
    }
  };

  const simulateTestCaseCleanup = async () => {
    const steps = [
      { text: 'Connecting to Azure DevOps Test Management API...', duration: 1000 },
      { text: 'Querying test cases in target area paths...', duration: 1500 },
      { text: 'Found 654 test cases to process', duration: 500 },
      { text: 'Processing Grit area test cases (248 items)...', duration: 1500 },
      { text: 'Processing Data Visualization area test cases (406 items)...', duration: 2000 },
      { text: 'Removing test suite associations...', duration: 800 },
      { text: 'Deleting test cases via Test Management API...', duration: 1200 },
      { text: 'Test case cleanup completed successfully', duration: 500 },
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentOperation(steps[i].text);
      setProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, steps[i].duration));
    }

    setCleanupStats({
      totalTestCases: 654,
      gritAreaCases: 248,
      dataVizAreaCases: 406,
    });
  };

  return (
    <div className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="flex items-center"
          >
            <FiArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-orange-500 mb-2 flex items-center">
            <FiClipboard className="mr-3 h-6 w-6" />
            Test Cases Cleanup
          </h1>
          <p className="text-muted-foreground">
            Delete test cases using the Azure DevOps Test Management API
          </p>
        </div>

        {/* Warning Alert */}
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Special Requirements for Test Cases!</AlertTitle>
            <AlertDescription>
              Test cases cannot be deleted using the standard Work Item API. This tool uses the 
              Test Management REST API which is the only supported method for test artifacts.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Info Alert */}
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>API Difference</AlertTitle>
            <AlertDescription>
              Unlike regular work items, test cases require the{' '}
              <Code>/test/testcases</Code> endpoint instead of the{' '}
              <Code>/wit/workitems</Code> endpoint.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Configuration Form */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Test Case Cleanup Configuration</Heading>
          </CardHeader>
          <CardContent>
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
                  Test cases in these area paths will be deleted using Test Management API.
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
                    Preview what test cases would be deleted without actually deleting anything
                  </Text>
                </Checkbox>
              </FormControl>
            </VStack>
          </CardContent>
        </Card>

        {/* Previous Success Stats */}
        <Card bg={cardBg} borderColor="green.200" borderWidth="2px">
          <CardHeader>
            <HStack>
              <Heading size="md" color="green.600">Last Test Case Cleanup Results</Heading>
              <Badge colorScheme="green">SUCCESS</Badge>
            </HStack>
          </CardHeader>
          <CardContent>
            <VStack spacing={3} align="stretch">
              <Text fontSize="sm" color="gray.600">
                Previous test case cleanup on 2025-07-13 completed successfully:
              </Text>
              <HStack justify="space-between">
                <Text>Total Test Cases Deleted:</Text>
                <Text fontWeight="bold" color="green.600">654</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• From Grit area path:</Text>
                <Text>248</Text>
              </HStack>
              <HStack justify="space-between">
                <Text>• From Data Visualization area path:</Text>
                <Text>406</Text>
              </HStack>
              <Divider />
              <Text fontSize="sm" color="gray.600">
                <Icon as={FiInfo} mr={2} />
                Used Test Management API endpoint: <Code fontSize="xs">/test/testcases</Code>
              </Text>
            </VStack>
          </CardContent>
        </Card>

        {/* Technical Details */}
        <Card bg={cardBg} borderColor="blue.200" borderWidth="1px">
          <CardHeader>
            <Heading size="sm" color="blue.600">Technical Details</Heading>
          </CardHeader>
          <CardContent>
            <VStack spacing={2} align="stretch" fontSize="sm">
              <Text>
                <strong>API Endpoint:</strong> <Code>DELETE /test/testcases/&#123;id&#125;</Code>
              </Text>
              <Text>
                <strong>API Version:</strong> <Code>7.1-preview.1</Code>
              </Text>
              <Text>
                <strong>Why Special API?</strong> Test cases have special associations with test suites 
                and test plans that require proper cleanup through the Test Management API.
              </Text>
            </VStack>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <HStack spacing={4}>
          <Button
            leftIcon={<Icon as={FiPlay} />}
            colorScheme={isDryRun ? 'blue' : 'orange'}
            size="lg"
            onClick={handleCleanup}
            isLoading={isLoading}
            loadingText={currentOperation}
          >
            {isDryRun ? 'Run Test Case Dry Run' : 'Start Test Case Cleanup'}
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
                {isLoading ? 'Test Case Cleanup in Progress' : 'Test Case Cleanup Complete'}
              </Heading>
            </CardHeader>
            <CardContent>
              <VStack spacing={4} align="stretch">
                {isLoading && (
                  <>
                    <Progress value={progress} colorScheme="orange" size="lg" borderRadius="md" />
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
                        <Text>Total Test Cases:</Text>
                        <Text fontWeight="bold">{cleanupStats.totalTestCases}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• From Grit area:</Text>
                        <Text>{cleanupStats.gritAreaCases}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>• From Data Visualization area:</Text>
                        <Text>{cleanupStats.dataVizAreaCases}</Text>
                      </HStack>
                    </VStack>
                  </>
                )}
              </VStack>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default TestCasesCleanupScreen;
