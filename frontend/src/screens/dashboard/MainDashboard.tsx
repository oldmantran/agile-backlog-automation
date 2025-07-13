import React from 'react';
import {
  Box,
  Grid,
  VStack,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Icon,
  useColorModeValue,
  Badge,
  HStack,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import {
  FiPlus,
  FiTrash2,
  FiRefreshCw,
  FiSearch,
  FiSettings,
  FiActivity,
  FiClipboard,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const successColor = useColorModeValue('green.500', 'green.300');

  const quickActions = [
    {
      title: 'Start New Project',
      description: 'Initialize a new agile project with automated backlog setup',
      icon: FiPlus,
      color: 'blue',
      path: '/project/create',
      isNew: true,
    },
    {
      title: 'Delete Work Items',
      description: 'Clean up work items from specific area paths',
      icon: FiTrash2,
      color: 'red',
      path: '/cleanup/work-items',
      warning: true,
    },
    {
      title: 'Delete Test Cases',
      description: 'Remove test cases using Test Management API',
      icon: FiClipboard,
      color: 'orange',
      path: '/cleanup/test-cases',
      warning: true,
    },
    {
      title: 'Run Backlog Sweeper',
      description: 'Execute automated backlog enhancement and quality checks',
      icon: FiRefreshCw,
      color: 'green',
      path: '/sweeper',
    },
    {
      title: 'Search Documentation',
      description: 'Find information across all markdown documentation',
      icon: FiSearch,
      color: 'purple',
      path: '/search',
    },
    {
      title: 'Project Settings',
      description: 'Configure Azure DevOps integration and project settings',
      icon: FiSettings,
      color: 'gray',
      path: '/settings',
    },
  ];

  const recentActivity = [
    {
      type: 'cleanup',
      title: 'Work Items Cleanup Completed',
      description: '1,141 work items deleted from Grit and Data Visualization areas',
      timestamp: '2025-07-13 00:32:27',
      status: 'success',
    },
    {
      type: 'cleanup',
      title: 'Test Cases Cleanup Completed',
      description: '654 test cases successfully removed using Test Management API',
      timestamp: '2025-07-13 07:47:00',
      status: 'success',
    },
  ];

  return (
    <Box p={6}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Agile Backlog Automation Dashboard
          </Heading>
          <Text color="gray.600">
            Manage your Azure DevOps projects with automated backlog enhancement tools
          </Text>
        </Box>

        {/* Recent Success Alert */}
        <Alert status="success" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Project Cleanup Complete!</AlertTitle>
            <AlertDescription>
              Successfully cleaned 1,795 work items from Backlog Automation project. 
              Your workspace is ready for fresh content.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Quick Actions Grid */}
        <Box>
          <Heading size="md" mb={4}>
            Quick Actions
          </Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
            {quickActions.map((action, index) => (
              <Card
                key={index}
                bg={cardBg}
                borderColor={borderColor}
                borderWidth="1px"
                cursor="pointer"
                transition="all 0.2s"
                _hover={{
                  transform: 'translateY(-2px)',
                  shadow: 'lg',
                  borderColor: `${action.color}.300`,
                }}
                onClick={() => navigate(action.path)}
              >
                <CardHeader pb={2}>
                  <HStack justify="space-between">
                    <HStack>
                      <Icon
                        as={action.icon}
                        color={`${action.color}.500`}
                        boxSize={5}
                      />
                      <Heading size="sm">{action.title}</Heading>
                    </HStack>
                    <HStack spacing={2}>
                      {action.isNew && (
                        <Badge colorScheme="blue" fontSize="xs">
                          NEW
                        </Badge>
                      )}
                      {action.warning && (
                        <Badge colorScheme="red" fontSize="xs">
                          CAUTION
                        </Badge>
                      )}
                    </HStack>
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <Text fontSize="sm" color="gray.600">
                    {action.description}
                  </Text>
                </CardBody>
              </Card>
            ))}
          </Grid>
        </Box>

        {/* Recent Activity */}
        <Box>
          <Heading size="md" mb={4}>
            Recent Activity
          </Heading>
          <VStack spacing={4} align="stretch">
            {recentActivity.map((activity, index) => (
              <Card key={index} bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardBody>
                  <HStack justify="space-between" align="start">
                    <VStack align="start" spacing={1} flex={1}>
                      <HStack>
                        <Icon as={FiActivity} color={successColor} />
                        <Text fontWeight="semibold">{activity.title}</Text>
                        <Badge colorScheme="green" fontSize="xs">
                          SUCCESS
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {activity.description}
                      </Text>
                    </VStack>
                    <Text fontSize="xs" color="gray.500">
                      {activity.timestamp}
                    </Text>
                  </HStack>
                </CardBody>
              </Card>
            ))}
          </VStack>
        </Box>

        {/* Quick Stats */}
        <Box>
          <Heading size="md" mb={4}>
            System Status
          </Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody textAlign="center">
                <Text fontSize="2xl" fontWeight="bold" color={successColor}>
                  1,795
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Items Cleaned
                </Text>
              </CardBody>
            </Card>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody textAlign="center">
                <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                  2
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Area Paths Cleared
                </Text>
              </CardBody>
            </Card>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody textAlign="center">
                <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                  Ready
                </Text>
                <Text fontSize="sm" color="gray.600">
                  System Status
                </Text>
              </CardBody>
            </Card>
          </Grid>
        </Box>
      </VStack>
    </Box>
  );
};

export default MainDashboard;
