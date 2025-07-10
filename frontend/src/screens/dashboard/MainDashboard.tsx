import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  SimpleGrid,
  Card,
  CardHeader,
  CardBody,
  Button,
  Icon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  HStack,
  VStack,
  Badge,
  useColorModeValue,
  Alert,
  AlertIcon,
  Spinner,
  Divider,
  useToast,
} from '@chakra-ui/react';
import { FiPlus, FiFileText, FiSettings, FiActivity, FiClock, FiCheckCircle, FiXCircle } from 'react-icons/fi';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { backlogApi } from '../../services/api/backlogApi';
import { jobsApi, JobInfo } from '../../services/api/jobsApi';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);

  // Check for job ID in URL params
  const jobIdFromUrl = searchParams.get('job');

  // Fetch jobs on component mount and set up polling
  useEffect(() => {
    fetchJobs();
    
    // Set up polling for job updates every 3 seconds
    const interval = setInterval(fetchJobs, 3000);
    
    return () => clearInterval(interval);
  }, []);

  // Show toast for new job if coming from project creation
  useEffect(() => {
    if (jobIdFromUrl) {
      toast({
        title: 'Job Started',
        description: `Your backlog generation job (${jobIdFromUrl}) is now running. You can monitor progress below.`,
        status: 'info',
        duration: 5000,
      });
    }
  }, [jobIdFromUrl, toast]);

  const fetchJobs = async () => {
    try {
      const jobsData = await jobsApi.getAllJobs();
      setJobs(jobsData);
      setIsLoadingJobs(false);
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError('Failed to load jobs');
      setIsLoadingJobs(false);
    }
  };

  const getJobIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return FiCheckCircle;
      case 'failed':
        return FiXCircle;
      case 'running':
        return FiActivity;
      default:
        return FiClock;
    }
  };

  const getJobColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      case 'running':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const activeJobs = jobs.filter(job => job.status === 'running' || job.status === 'queued');
  const completedJobs = jobs.filter(job => job.status === 'completed');
  const failedJobs = jobs.filter(job => job.status === 'failed');

  const handleNewProject = () => {
    navigate('/project/new');
  };

  const handleViewTemplates = async () => {
    try {
      setIsLoading(true);
      const templates = await backlogApi.getTemplates();
      console.log('Available templates:', templates);
      setIsLoading(false);
    } catch (err) {
      setError('Failed to load templates');
      setIsLoading(false);
    }
  };

  return (
    <Box bg={bgColor} minH="100vh" p={{ base: 4, md: 8 }}>
      <Heading mb={6} size="xl">Dashboard</Heading>
      
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          {error}
        </Alert>
      )}
      
      {/* Quick Actions */}
      <Flex 
        mb={6}
        direction={{ base: 'column', sm: 'row' }} 
        gap={4}
      >
        <Button
          leftIcon={<Icon as={FiPlus} />}
          colorScheme="brand"
          size="lg"
          onClick={handleNewProject}
        >
          New Project
        </Button>
        <Button
          leftIcon={<Icon as={FiFileText} />}
          variant="outline"
          size="lg"
          onClick={handleViewTemplates}
          isLoading={isLoading}
        >
          View Templates
        </Button>
        <Button
          leftIcon={<Icon as={FiSettings} />}
          variant="outline"
          size="lg"
        >
          Settings
        </Button>
      </Flex>

      {/* Stats Grid */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Total Projects</StatLabel>
              <StatNumber>{jobs.length}</StatNumber>
              <StatHelpText>
                {jobs.length === 0 ? 'No projects yet' : 'Projects created'}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Active Generations</StatLabel>
              <StatNumber>{activeJobs.length}</StatNumber>
              <StatHelpText>
                <Icon as={FiActivity} mr={1} />
                {activeJobs.length === 0 ? 'No active jobs' : 'Running jobs'}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Completed</StatLabel>
              <StatNumber>{completedJobs.length}</StatNumber>
              <StatHelpText>
                <Icon as={FiCheckCircle} mr={1} />
                Successfully generated
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Success Rate</StatLabel>
              <StatNumber>
                {jobs.length > 0 ? Math.round((completedJobs.length / jobs.length) * 100) : '--'}%
              </StatNumber>
              <StatHelpText>
                {failedJobs.length > 0 ? `${failedJobs.length} failed` : 'All successful'}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Active Jobs Section */}
      {isLoadingJobs && (
        <Box mb={8} textAlign="center">
          <Spinner size="lg" />
          <Text mt={2}>Loading job status...</Text>
        </Box>
      )}

      {activeJobs.length > 0 && (
        <Box mb={8}>
          <Heading size="lg" mb={4}>
            <Icon as={FiActivity} mr={2} />
            Active Generation Jobs
          </Heading>
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
            {activeJobs.map((job) => (
              <Card key={job.jobId} bg={cardBg} borderLeft="4px solid" borderLeftColor="blue.400">
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold">Project: {job.projectId}</Text>
                      <Text fontSize="sm" color="gray.500">Job ID: {job.jobId}</Text>
                    </VStack>
                    <Badge colorScheme={getJobColor(job.status)}>
                      {job.status}
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="stretch" spacing={3}>
                    <HStack>
                      <Icon as={getJobIcon(job.status)} />
                      <Text fontSize="sm">
                        {job.currentAgent && `Agent: ${job.currentAgent}`}
                      </Text>
                    </HStack>
                    <Text fontSize="sm" color="gray.600">
                      {job.currentAction || 'Processing...'}
                    </Text>
                    <Progress 
                      value={job.progress || 0} 
                      colorScheme="blue" 
                      size="sm"
                      hasStripe
                      isAnimated
                    />
                    <HStack justify="space-between">
                      <Text fontSize="xs" color="gray.500">
                        {job.progress || 0}% complete
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        Started: {new Date(job.startTime).toLocaleTimeString()}
                      </Text>
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        </Box>
      )}

      {/* Completed Jobs Section */}
      {completedJobs.length > 0 && (
        <Box mb={8}>
          <Heading size="lg" mb={4}>
            <Icon as={FiCheckCircle} mr={2} />
            Completed Backlogs
          </Heading>
          <SimpleGrid columns={{ base: 1, lg: 2, xl: 3 }} spacing={4}>
            {completedJobs.map((job) => (
              <Card key={job.jobId} bg={cardBg} borderLeft="4px solid" borderLeftColor="green.400">
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold">Project: {job.projectId}</Text>
                      <Text fontSize="sm" color="gray.500">Job ID: {job.jobId}</Text>
                    </VStack>
                    <Badge colorScheme="green">
                      Completed
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between">
                      <Text fontSize="sm" color="gray.600">
                        Started: {new Date(job.startTime).toLocaleTimeString()}
                      </Text>
                      {job.endTime && (
                        <Text fontSize="sm" color="gray.600">
                          Completed: {new Date(job.endTime).toLocaleTimeString()}
                        </Text>
                      )}
                    </HStack>
                    <Progress value={100} colorScheme="green" size="sm" />
                    <Button 
                      size="sm" 
                      variant="outline" 
                      colorScheme="green"
                      onClick={() => {
                        // Navigate to project details or Azure DevOps
                        toast({
                          title: "Backlog Generated",
                          description: "Check Azure DevOps for your generated backlog items",
                          status: "info",
                          duration: 3000,
                        });
                      }}
                    >
                      View Results
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        </Box>
      )}

      {/* Failed Jobs Section */}
      {failedJobs.length > 0 && (
        <Box mb={8}>
          <Heading size="lg" mb={4}>
            <Icon as={FiXCircle} mr={2} />
            Failed Generations
          </Heading>
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
            {failedJobs.map((job) => (
              <Card key={job.jobId} bg={cardBg} borderLeft="4px solid" borderLeftColor="red.400">
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold">Project: {job.projectId}</Text>
                      <Text fontSize="sm" color="gray.500">Job ID: {job.jobId}</Text>
                    </VStack>
                    <Badge colorScheme="red">
                      Failed
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="stretch" spacing={3}>
                    <Text fontSize="sm" color="red.600">
                      Error: {job.error || 'Unknown error occurred'}
                    </Text>
                    <HStack justify="space-between">
                      <Text fontSize="sm" color="gray.600">
                        Started: {new Date(job.startTime).toLocaleTimeString()}
                      </Text>
                      {job.endTime && (
                        <Text fontSize="sm" color="gray.600">
                          Failed: {new Date(job.endTime).toLocaleTimeString()}
                        </Text>
                      )}
                    </HStack>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      colorScheme="red"
                      onClick={() => {
                        // Retry logic could be added here
                        toast({
                          title: "Retry Feature",
                          description: "Retry functionality coming soon",
                          status: "info",
                          duration: 2000,
                        });
                      }}
                    >
                      Retry
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        </Box>
      )}

      {/* Empty State */}
      {!isLoadingJobs && jobs.length === 0 && (
        <Box>
          <Heading size="lg" mb={4}>Get Started</Heading>
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={4} align="center" py={8}>
                <Icon as={FiPlus} size="48px" color="gray.400" />
                <Text color="gray.500">No projects yet</Text>
                <Text fontSize="sm" color="gray.400" textAlign="center">
                  Create your first project to start generating comprehensive backlogs with AI automation
                </Text>
                <Button 
                  colorScheme="blue" 
                  size="lg"
                  onClick={handleNewProject}
                >
                  Create Your First Project
                </Button>
              </VStack>
            </CardBody>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default MainDashboard;
