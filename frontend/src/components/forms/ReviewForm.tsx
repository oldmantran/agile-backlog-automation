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
  
  const visionStatement = initialData.visionStatement || 'No vision statement provided';
  const businessObjectives = initialData.businessObjectives || [];
  const successMetrics = initialData.successMetrics || [];
  const targetAudience = initialData.targetAudience || 'Not specified';
  
  const hasAzureConfig = initialData.organizationUrl && initialData.project;
  
  const handleSubmit = async () => {
    setIsGenerating(true);
    
    // Simulate API call for creating backlog
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      onNext(initialData);
    } catch (error) {
      console.error('Error generating backlog:', error);
    } finally {
      setIsGenerating(false);
    }
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
        <Heading size="md" color={accentColor}>Review Project Information</Heading>
        
        <Box>
          <Heading size="sm" mb={2}>Project Basics</Heading>
          <List spacing={2}>
            <ListItem>
              <HStack>
                <ListIcon as={FiCheck} color="green.500" />
                <Text fontWeight="bold">Name:</Text>
                <Text>{projectName}</Text>
              </HStack>
            </ListItem>
            <ListItem>
              <HStack alignItems="flex-start">
                <ListIcon as={FiCheck} color="green.500" mt={1} />
                <Text fontWeight="bold">Description:</Text>
                <Text flex="1">{projectDescription}</Text>
              </HStack>
            </ListItem>
            <ListItem>
              <HStack>
                <ListIcon as={FiCheck} color="green.500" />
                <Text fontWeight="bold">Domain:</Text>
                <Badge colorScheme="blue">{domain}</Badge>
              </HStack>
            </ListItem>
            <ListItem>
              <HStack>
                <ListIcon as={FiCheck} color="green.500" />
                <Text fontWeight="bold">Team Size:</Text>
                <Text>{teamSize} people</Text>
              </HStack>
            </ListItem>
            <ListItem>
              <HStack>
                <ListIcon as={FiCheck} color="green.500" />
                <Text fontWeight="bold">Timeline:</Text>
                <Text>{timeline}</Text>
              </HStack>
            </ListItem>
          </List>
        </Box>
        
        <Divider />
        
        <Box>
          <Heading size="sm" mb={2}>Project Vision</Heading>
          <List spacing={2}>
            <ListItem>
              <HStack alignItems="flex-start">
                <ListIcon as={FiCheck} color="green.500" mt={1} />
                <Text fontWeight="bold">Vision:</Text>
                <Text flex="1">{visionStatement}</Text>
              </HStack>
            </ListItem>
            
            <ListItem>
              <VStack align="stretch">
                <HStack>
                  <ListIcon as={FiCheck} color="green.500" />
                  <Text fontWeight="bold">Business Objectives:</Text>
                </HStack>
                <Box pl={8}>
                  {businessObjectives.length > 0 ? (
                    <List>
                      {businessObjectives.map((objective: string, index: number) => (
                        <ListItem key={index}>• {objective}</ListItem>
                      ))}
                    </List>
                  ) : (
                    <Text color="gray.500">No business objectives specified</Text>
                  )}
                </Box>
              </VStack>
            </ListItem>
            
            <ListItem>
              <VStack align="stretch">
                <HStack>
                  <ListIcon as={FiCheck} color="green.500" />
                  <Text fontWeight="bold">Success Metrics:</Text>
                </HStack>
                <Box pl={8}>
                  {successMetrics.length > 0 ? (
                    <List>
                      {successMetrics.map((metric: string, index: number) => (
                        <ListItem key={index}>• {metric}</ListItem>
                      ))}
                    </List>
                  ) : (
                    <Text color="gray.500">No success metrics specified</Text>
                  )}
                </Box>
              </VStack>
            </ListItem>
          </List>
        </Box>
        
        <Divider />
        
        <Box>
          <Heading size="sm" mb={2}>Azure DevOps Configuration</Heading>
          {hasAzureConfig ? (
            <List spacing={2}>
              <ListItem>
                <HStack>
                  <ListIcon as={FiCheck} color="green.500" />
                  <Text fontWeight="bold">Organization:</Text>
                  <Text>{initialData.organizationUrl}</Text>
                </HStack>
              </ListItem>
              <ListItem>
                <HStack>
                  <ListIcon as={FiCheck} color="green.500" />
                  <Text fontWeight="bold">Project:</Text>
                  <Text>{initialData.project}</Text>
                </HStack>
              </ListItem>
              {initialData.areaPath && (
                <ListItem>
                  <HStack>
                    <ListIcon as={FiCheck} color="green.500" />
                    <Text fontWeight="bold">Area Path:</Text>
                    <Text>{initialData.areaPath}</Text>
                  </HStack>
                </ListItem>
              )}
              {initialData.iterationPath && (
                <ListItem>
                  <HStack>
                    <ListIcon as={FiCheck} color="green.500" />
                    <Text fontWeight="bold">Iteration Path:</Text>
                    <Text>{initialData.iterationPath}</Text>
                  </HStack>
                </ListItem>
              )}
            </List>
          ) : (
            <Alert status="warning">
              <AlertIcon />
              <Text>Azure DevOps configuration is incomplete. Backlog will be generated but not pushed to Azure DevOps.</Text>
            </Alert>
          )}
        </Box>
        
        <Accordion allowToggle>
          <AccordionItem border="none">
            <AccordionButton px={0}>
              <Heading size="sm" flex="1" textAlign="left">AI Configuration</Heading>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4} pl={4}>
              <List spacing={2}>
                <ListItem>
                  <HStack>
                    <Text fontWeight="bold">Model:</Text>
                    <Text>{initialData.modelType || 'gpt4o'}</Text>
                  </HStack>
                </ListItem>
                <ListItem>
                  <Text fontWeight="bold" mb={1}>Features:</Text>
                  <Flex wrap="wrap" gap={2}>
                    {initialData.generateAcceptanceCriteria && (
                      <Badge colorScheme="green">Acceptance Criteria</Badge>
                    )}
                    {initialData.generateTestCases && (
                      <Badge colorScheme="green">Test Cases</Badge>
                    )}
                    {initialData.estimateComplexity && (
                      <Badge colorScheme="green">Story Points</Badge>
                    )}
                    {initialData.enableWorkItemLinking && (
                      <Badge colorScheme="green">Work Item Linking</Badge>
                    )}
                  </Flex>
                </ListItem>
              </List>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
        
        <HStack justify="space-between" pt={4}>
          {onPrevious && (
            <Button 
              onClick={onPrevious}
              size="lg"
              isDisabled={isGenerating}
            >
              Previous
            </Button>
          )}
          <Button 
            colorScheme="brand" 
            size="lg" 
            onClick={handleSubmit}
            ml="auto"
            minW="200px"
            isLoading={isGenerating}
            loadingText="Generating Backlog"
            leftIcon={isGenerating ? undefined : <FiCheck />}
          >
            Generate Backlog
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

export default ReviewForm;
