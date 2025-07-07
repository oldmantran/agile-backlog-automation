import React from 'react';
import {
  Box,
  Flex,
  Text,
  Button,
  Stack,
  Container,
  Heading,
  Image,
  useColorModeValue,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

const WelcomeScreen: React.FC = () => {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');
  
  return (
    <Flex minH="100vh" bg={bgColor} direction="column">
      <Container maxW="container.xl" flex="1">
        <Flex 
          direction={{ base: 'column', md: 'row' }}
          align="center" 
          justify="center"
          minH="100vh"
          py={10}
          gap={8}
        >
          <Stack spacing={6} maxW="lg">
            <Heading
              lineHeight={1.1}
              fontWeight={600}
              fontSize={{ base: '3xl', sm: '4xl', lg: '5xl' }}
            >
              <Text
                as="span"
                position="relative"
                color="brand.500"
              >
                Agile Backlog Automation
              </Text>
              <br />
              <Text as="span" color="accent.500">
                AI-Powered Project Planning
              </Text>
            </Heading>
            
            <Text color="gray.500" fontSize={{ base: 'md', lg: 'lg' }}>
              Create comprehensive product backlogs in minutes instead of days.
              Our AI-powered system helps project managers, business analysts,
              and product owners create high-quality backlogs with minimal effort.
            </Text>
            
            <Stack spacing={6} direction={{ base: 'column', sm: 'row' }}>
              <Button
                size="lg"
                fontWeight="bold"
                px={6}
                colorScheme="brand"
                onClick={() => navigate('/project/new')}
              >
                Create New Project
              </Button>
              
              <Button
                size="lg"
                fontWeight="bold"
                px={6}
                variant="outline"
                onClick={() => navigate('/dashboard')}
              >
                View Dashboard
              </Button>
            </Stack>
          </Stack>
          
          <Box
            rounded="2xl"
            bg={cardBg}
            boxShadow="xl"
            p={6}
            overflow="hidden"
            minW={{ base: 'full', md: '400px' }}
            maxW={{ base: 'full', md: '450px' }}
          >
            {/* Placeholder for an illustration or screenshot */}
            <Box height="300px" bg="gray.200" rounded="lg">
              {/* Replace with actual image */}
              <Text p={4} textAlign="center">Project Dashboard Preview</Text>
            </Box>
          </Box>
        </Flex>
      </Container>
    </Flex>
  );
};

export default WelcomeScreen;
