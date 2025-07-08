import React from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  Heading,
  Badge,
  Divider,
  List,
  ListItem,
  ListIcon,
  useColorModeValue,
  Alert,
  AlertIcon,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Flex,
  Spinner,
} from '@chakra-ui/react';
import { FiCheck, FiAlertTriangle } from 'react-icons/fi';

interface ReviewFormProps {
  onNext: (data: any) => void;
  onPrevious?: () => void;
  initialData?: any;
}

const ReviewForm: React.FC<ReviewFormProps> = ({
  onNext,
  onPrevious,
  initialData = {},
}) => {
  const [isGenerating, setIsGenerating] = React.useState(false);
  
  const bgColor = useColorModeValue('white', 'gray.700');
  const accentColor = useColorModeValue('brand.500', 'brand.300');
  
  // Extract data from initial data
  const projectName = initialData.name || 'Untitled Project';
  const projectDescription = initialData.description || 'No description provided';
  const domain = initialData.domain || 'Not specified';
  const teamSize = initialData.teamSize || 0;
  const timeline = initialData.timeline || 'Not specified';
  const visionStatement = initialData.visionStatement || 'Not provided';
  const businessObjectives = initialData.businessObjectives || [];
  const azureConfig = initialData.azureConfig || {};

  const handleGenerateBacklog = () => {
    setIsGenerating(true);
    
    // Simulate API call with a timeout
    setTimeout(() => {
      setIsGenerating(false);
      onNext(initialData);
    }, 2000);
  };
  
  return (
    <Box
      bg={bgColor}
      p={6}
      borderRadius="lg"
      boxShadow="md"
      width="full"
    >
      <VStack spacing={6} align="stretch">
        <Heading size="md" color={accentColor}>Review Project Details</Heading>
        
        <Alert status="info">
          <AlertIcon />
          Please review your project configuration before generating the backlog
        </Alert>
        
        <Accordion defaultIndex={[0]} allowMultiple>
          <AccordionItem>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left" fontWeight="semibold">
                  Project Basics
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack align="start" spacing={2}>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Project Name:</Text>
                  <Text>{projectName}</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Description:</Text>
                  <Text>{projectDescription}</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Domain:</Text>
                  <Badge>{domain}</Badge>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Team Size:</Text>
                  <Text>{teamSize} people</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Timeline:</Text>
                  <Text>{timeline}</Text>
                </Flex>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
          
          <AccordionItem>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left" fontWeight="semibold">
                  Vision & Objectives
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack align="start" spacing={4}>
                <Box width="full">
                  <Text fontWeight="semibold" mb={1}>Vision Statement:</Text>
                  <Text>{visionStatement}</Text>
                </Box>
                
                <Box width="full">
                  <Text fontWeight="semibold" mb={1}>Business Objectives:</Text>
                  <List spacing={1}>
                    {businessObjectives.length > 0 ? 
                      businessObjectives.map((obj: string, index: number) => (
                        <ListItem key={index}>
                          <ListIcon as={FiCheck} color="green.500" />
                          {obj}
                        </ListItem>
                      )) : 
                      <Text color="gray.500">No objectives specified</Text>
                    }
                  </List>
                </Box>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
          
          <AccordionItem>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left" fontWeight="semibold">
                  Azure DevOps Configuration
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack align="start" spacing={2}>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Organization URL:</Text>
                  <Text>{azureConfig.organizationUrl || 'Not configured'}</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Project:</Text>
                  <Text>{azureConfig.project || 'Not configured'}</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Area Path:</Text>
                  <Text>{azureConfig.areaPath || 'Not configured'}</Text>
                </Flex>
                <Flex justify="space-between" width="full">
                  <Text fontWeight="semibold">Iteration Path:</Text>
                  <Text>{azureConfig.iterationPath || 'Not configured'}</Text>
                </Flex>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
        
        <Divider />
        
        <HStack justify="space-between">
          <Button 
            variant="outline" 
            onClick={onPrevious}
            isDisabled={isGenerating}
          >
            Previous
          </Button>
          
          <Button 
            colorScheme="brand" 
            onClick={handleGenerateBacklog}
            isLoading={isGenerating}
            loadingText="Generating"
            rightIcon={isGenerating ? undefined : <FiCheck />}
          >
            Generate Backlog
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

export default ReviewForm;
