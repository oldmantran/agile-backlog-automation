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
  Card,
  CardHeader,
  CardBody,
} from '@chakra-ui/react';
import { FiCheck, FiAlertTriangle, FiPlay } from 'react-icons/fi';

interface ReviewFormProps {
  onNext?: (data: any) => void;
  onPrevious?: () => void;
  onSubmit?: (data: any) => void;
  initialData?: any;
  isLoading?: boolean;
}

const ReviewForm: React.FC<ReviewFormProps> = ({
  onNext,
  onPrevious,
  onSubmit,
  initialData = {},
  isLoading = false,
}) => {
  const bgColor = useColorModeValue('white', 'gray.700');
  const cardBg = useColorModeValue('gray.50', 'gray.600');
  const accentColor = useColorModeValue('brand.500', 'brand.300');
  
  // Extract data from initial data - handle nested structure
  const basics = initialData.basics || {};
  const vision = initialData.vision || {};
  const azure = initialData.azureConfig || {};
  
  const projectName = basics.name || 'Untitled Project';
  const projectDescription = basics.description || 'No description provided';
  const domain = basics.domain || 'Not specified';
  const teamSize = basics.teamSize || 0;
  const timeline = basics.timeline || 'Not specified';
  const visionStatement = vision.visionStatement || 'Not provided';
  const businessObjectives = vision.businessObjectives || [];
  const azureOrg = azure.organizationUrl || 'Not configured';
  const azureProject = azure.project || 'Not configured';

  const handleGenerate = () => {
    if (onSubmit) {
      onSubmit({
        confirmed: true,
        timestamp: new Date().toISOString()
      });
    } else if (onNext) {
      onNext({
        confirmed: true,
        timestamp: new Date().toISOString()
      });
    }
  };

  const isConfigurationValid = () => {
    const hasBasics = basics.name && basics.description && basics.domain;
    const hasVision = vision.visionStatement;
    // Azure config is valid if either manual config is provided OR useExistingConfig is true
    const hasAzureConfig = (azure.organizationUrl && azure.project) || azure.useExistingConfig;
    
    return hasBasics && hasVision && hasAzureConfig;
  };

  return (
    <Box p={6} bg={bgColor} borderRadius="lg" shadow="sm">
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Review & Generate</Heading>
          <Text color="gray.600">
            Review your project configuration and start the backlog generation process.
          </Text>
        </Box>

        {!isConfigurationValid() && (
          <Alert status="warning">
            <AlertIcon />
            Please complete all required fields before generating your backlog.
          </Alert>
        )}

        <Accordion allowToggle>
          {/* Project Basics */}
          <AccordionItem>
            <AccordionButton>
              <Box flex="1" textAlign="left">
                <HStack>
                  <Text fontWeight="bold">Project Basics</Text>
                  <Badge colorScheme={basics.name ? "green" : "red"}>
                    {basics.name ? "Complete" : "Incomplete"}
                  </Badge>
                </HStack>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <Card bg={cardBg}>
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <Box>
                      <Text fontWeight="semibold">Project Name:</Text>
                      <Text>{projectName}</Text>
                    </Box>
                    <Box>
                      <Text fontWeight="semibold">Description:</Text>
                      <Text>{projectDescription}</Text>
                    </Box>
                    <HStack>
                      <Box>
                        <Text fontWeight="semibold">Domain:</Text>
                        <Text>{domain}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="semibold">Team Size:</Text>
                        <Text>{teamSize} members</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="semibold">Timeline:</Text>
                        <Text>{timeline}</Text>
                      </Box>
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>
            </AccordionPanel>
          </AccordionItem>

          {/* Vision & Goals */}
          <AccordionItem>
            <AccordionButton>
              <Box flex="1" textAlign="left">
                <HStack>
                  <Text fontWeight="bold">Vision & Goals</Text>
                  <Badge colorScheme={vision.visionStatement ? "green" : "red"}>
                    {vision.visionStatement ? "Complete" : "Incomplete"}
                  </Badge>
                </HStack>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <Card bg={cardBg}>
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <Box>
                      <Text fontWeight="semibold">Vision Statement:</Text>
                      <Text>{visionStatement}</Text>
                    </Box>
                    {businessObjectives.length > 0 && (
                      <Box>
                        <Text fontWeight="semibold">Business Objectives:</Text>
                        <List spacing={1}>
                          {businessObjectives.map((objective: string, index: number) => (
                            <ListItem key={index}>
                              <ListIcon as={FiCheck} color="green.500" />
                              {objective}
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </AccordionPanel>
          </AccordionItem>

          {/* Azure DevOps Configuration */}
          <AccordionItem>
            <AccordionButton>
              <Box flex="1" textAlign="left">
                <HStack>
                  <Text fontWeight="bold">Azure DevOps Setup</Text>
                  <Badge colorScheme={(azure.organizationUrl || azure.useExistingConfig) ? "green" : "red"}>
                    {(azure.organizationUrl || azure.useExistingConfig) ? "Complete" : "Incomplete"}
                  </Badge>
                </HStack>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <Card bg={cardBg}>
                <CardBody>
                  {azure.useExistingConfig ? (
                    <Alert status="info">
                      <AlertIcon />
                      <Box>
                        <Text fontWeight="bold">Using Environment Configuration</Text>
                        <Text fontSize="sm">
                          Azure DevOps settings will be loaded from your environment configuration.
                        </Text>
                      </Box>
                    </Alert>
                  ) : (
                    <VStack align="stretch" spacing={3}>
                      <Box>
                        <Text fontWeight="semibold">Organization:</Text>
                        <Text>{azureOrg}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="semibold">Project:</Text>
                        <Text>{azureProject}</Text>
                      </Box>
                    </VStack>
                  )}
                </CardBody>
              </Card>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>

        {/* Generation Preview */}
        <Alert status="info">
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">What happens next?</Text>
            <Text fontSize="sm">
              Our AI agents will analyze your project requirements and generate a comprehensive 
              backlog including epics, features, user stories, and tasks tailored to your domain.
            </Text>
          </Box>
        </Alert>

        <Divider />

        {/* Action Buttons */}
        <HStack justify="space-between">
          <Button
            variant="outline"
            onClick={onPrevious}
            isDisabled={isLoading}
          >
            Previous
          </Button>
          
          <Button
            colorScheme="brand"
            size="lg"
            onClick={handleGenerate}
            isLoading={isLoading}
            loadingText="Generating..."
            rightIcon={isLoading ? undefined : <FiPlay />}
            isDisabled={!isConfigurationValid()}
          >
            Generate Backlog
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

export default ReviewForm;
