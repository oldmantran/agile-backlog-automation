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
} from '@chakra-ui/react';
import { FiPlus, FiFileText, FiSettings, FiActivity } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { backlogApi } from '../../services/api/backlogApi';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJobs, setActiveJobs] = useState<any[]>([]);

  useEffect(() => {
    // Check for any active generation jobs in localStorage
    const storedJobs = localStorage.getItem('activeJobs');
    if (storedJobs) {
      setActiveJobs(JSON.parse(storedJobs));
    }
  }, []);

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
              <StatNumber>0</StatNumber>
              <StatHelpText>No projects yet</StatHelpText>
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
                Running jobs
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Generated Items</StatLabel>
              <StatNumber>0</StatNumber>
              <StatHelpText>Backlog items created</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Success Rate</StatLabel>
              <StatNumber>--</StatNumber>
              <StatHelpText>Generation success</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Box mb={8}>
          <Heading size="lg" mb={4}>Active Generation Jobs</Heading>
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
            {activeJobs.map((job) => (
              <Card key={job.jobId} bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <Text fontWeight="bold">Job {job.jobId}</Text>
                    <Badge 
                      colorScheme={
                        job.status === 'completed' ? 'green' :
                        job.status === 'failed' ? 'red' :
                        job.status === 'running' ? 'blue' : 'gray'
                      }
                    >
                      {job.status}
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="stretch" spacing={3}>
                    <Text fontSize="sm" color="gray.600">
                      {job.currentAction || 'Processing...'}
                    </Text>
                    <Progress 
                      value={job.progress || 0} 
                      colorScheme="brand" 
                      size="sm"
                    />
                    <Text fontSize="xs" color="gray.500">
                      {job.progress || 0}% complete
                    </Text>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        </Box>
      )}

      {/* Recent Projects */}
      <Box>
        <Heading size="lg" mb={4}>Recent Projects</Heading>
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="center" py={8}>
              <Icon as={FiPlus} size="48px" color="gray.400" />
              <Text color="gray.500">No projects yet</Text>
              <Button 
                colorScheme="brand" 
                variant="outline"
                onClick={handleNewProject}
              >
                Create Your First Project
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Box>
    </Box>
  );
};

export default MainDashboard;
