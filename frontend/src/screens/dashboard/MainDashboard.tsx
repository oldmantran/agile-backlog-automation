import React from 'react';
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
} from '@chakra-ui/react';
import { FiPlus, FiFileText, FiSettings } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');
  
  return (
    <Box bg={bgColor} minH="100vh" p={{ base: 4, md: 8 }}>
      <Heading mb={6} size="xl">Dashboard</Heading>
      
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
          onClick={() => navigate('/project/new')}
        >
          New Project
        </Button>
        <Button
          leftIcon={<Icon as={FiFileText} />}
          variant="outline"
          size="lg"
        >
          View Templates
        </Button>
        <Button
          leftIcon={<Icon as={FiSettings} />}
          variant="ghost"
          size="lg"
          onClick={() => navigate('/settings')}
        >
          Settings
        </Button>
      </Flex>
      
      {/* Stats Overview */}
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} mb={8}>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Total Projects</StatLabel>
              <StatNumber>5</StatNumber>
              <StatHelpText>3 Active, 2 Completed</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Generated Work Items</StatLabel>
              <StatNumber>253</StatNumber>
              <StatHelpText>Last 30 days</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>System Status</StatLabel>
              <HStack mt={2}>
                <Badge colorScheme="green">Azure Connected</Badge>
                <Badge colorScheme="green">Agents Active</Badge>
              </HStack>
              <StatHelpText>All systems operational</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Recent Projects */}
      <Box mb={8}>
        <Heading size="md" mb={4}>Recent Projects</Heading>
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          {/* Project Card 1 */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Data Visualization System</Heading>
            </CardHeader>
            <CardBody>
              <VStack align="start" spacing={3}>
                <Text>Created: 2 days ago</Text>
                <Progress value={75} colorScheme="brand" w="full" />
                <HStack justify="space-between" w="full">
                  <Text color="gray.500">75% Complete</Text>
                  <Badge colorScheme="orange">In Progress</Badge>
                </HStack>
                <Button size="sm" variant="outline" colorScheme="brand" w="full">
                  View Details
                </Button>
              </VStack>
            </CardBody>
          </Card>
          
          {/* Project Card 2 */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Mobile Customer Portal</Heading>
            </CardHeader>
            <CardBody>
              <VStack align="start" spacing={3}>
                <Text>Created: 1 week ago</Text>
                <Progress value={100} colorScheme="green" w="full" />
                <HStack justify="space-between" w="full">
                  <Text color="gray.500">100% Complete</Text>
                  <Badge colorScheme="green">Completed</Badge>
                </HStack>
                <Button size="sm" variant="outline" colorScheme="brand" w="full">
                  View Details
                </Button>
              </VStack>
            </CardBody>
          </Card>
          
          {/* Project Card 3 */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">API Integration Service</Heading>
            </CardHeader>
            <CardBody>
              <VStack align="start" spacing={3}>
                <Text>Created: 3 days ago</Text>
                <Progress value={40} colorScheme="brand" w="full" />
                <HStack justify="space-between" w="full">
                  <Text color="gray.500">40% Complete</Text>
                  <Badge colorScheme="orange">In Progress</Badge>
                </HStack>
                <Button size="sm" variant="outline" colorScheme="brand" w="full">
                  View Details
                </Button>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>
      </Box>
    </Box>
  );
};

export default MainDashboard;
