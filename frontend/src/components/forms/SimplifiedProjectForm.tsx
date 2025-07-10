import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  HStack,
  FormHelperText,
  useColorModeValue,
  Text,
  Heading,
  Divider,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

interface SimplifiedProjectFormProps {
  onSubmit: (data: any) => void;
  isSubmitting?: boolean;
  initialData?: any;
}

const SimplifiedProjectForm: React.FC<SimplifiedProjectFormProps> = ({
  onSubmit,
  isSubmitting = false,
  initialData = {},
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      visionStatement: initialData.visionStatement || '',
      adoProject: initialData.adoProject || '',
      areaPath: initialData.areaPath || '',
      iterationPath: initialData.iterationPath || '',
    }
  });
  
  const bgColor = useColorModeValue('white', 'gray.700');
  
  const onFormSubmit = (data: any) => {
    // Transform data to match backend expectations
    // Extract organization and project from input (handles both "org/project" and "project" formats)
    const projectParts = data.adoProject.includes('/') ? data.adoProject.split('/') : [data.adoProject.split('.')[0], data.adoProject];
    const organization = projectParts[0];
    const project = projectParts[1] || projectParts[0];
    
    const projectData = {
      basics: {
        name: "AI Generated Project", // Default name - extracted from vision by AI
        description: data.visionStatement.substring(0, 200) + "...", // Extract from vision
        domain: "software_development" // Default domain - not used by agents
      },
      vision: {
        visionStatement: data.visionStatement,
        businessObjectives: ["TBD"], // Will be extracted by AI from vision statement
        successMetrics: ["TBD"], // Will be extracted by AI from vision statement
        targetAudience: "end users" // Default - will be extracted by AI from vision
      },
      azureConfig: {
        organizationUrl: `https://dev.azure.com/${organization}`, // Extract from project
        personalAccessToken: "", // Will be loaded from .env
        project: project, // Extract project name
        areaPath: data.areaPath,
        iterationPath: data.iterationPath
      }
    };
    
    onSubmit(projectData);
  };
  
  return (
    <Box
      bg={bgColor}
      p={8}
      borderRadius="xl"
      boxShadow="lg"
      width="full"
      maxWidth="800px"
      mx="auto"
    >
      <VStack spacing={6} align="stretch">
        <Box textAlign="center">
          <Heading size="lg" mb={2}>
            Create Agile Backlog
          </Heading>
          <Text color="gray.500">
            Enter your product vision and Azure DevOps details to generate a comprehensive backlog
          </Text>
        </Box>
        
        <Divider />
        
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <VStack spacing={6} align="stretch">
            {/* Vision Statement - The core input */}
            <FormControl isRequired isInvalid={!!errors.visionStatement}>
              <FormLabel fontSize="lg" fontWeight="semibold">
                Product Vision & Requirements
              </FormLabel>
              <Textarea 
                {...register('visionStatement', { 
                  required: 'Product vision is required',
                  minLength: { value: 50, message: 'Vision must be at least 50 characters' }
                })} 
                placeholder="Describe your product vision, including goals, objectives, target audience, success metrics, and key features. Be as comprehensive as possible - this will drive the entire backlog generation.

Example: Create a comprehensive ride-sharing platform that connects drivers and passengers with real-time matching, secure payments, and intelligent routing. Target urban commuters and part-time drivers seeking flexible income. Success measured by: 50K+ active users in 6 months, 90%+ ride completion rate, $2M+ annual revenue. Key features include driver background checks, real-time GPS tracking, in-app payments, surge pricing, and customer ratings."
                size="lg"
                rows={8}
                resize="vertical"
              />
              {errors.visionStatement && (
                <FormHelperText color="red.500">
                  {errors.visionStatement.message as string}
                </FormHelperText>
              )}
              <FormHelperText>
                Include your vision, goals, target audience, success metrics, and key requirements. The AI will extract objectives, metrics, and target audience from this comprehensive description.
              </FormHelperText>
            </FormControl>
            
            <Divider />
            
            {/* Azure DevOps Configuration */}
            <Box>
              <Heading size="md" mb={4}>
                Azure DevOps Configuration
              </Heading>
              
              <VStack spacing={4} align="stretch">
                  <FormControl isRequired isInvalid={!!errors.adoProject}>
                    <FormLabel>Azure DevOps Project</FormLabel>
                    <Input 
                      {...register('adoProject', { 
                        required: 'Azure DevOps project is required'
                      })} 
                      placeholder="organization/project or project-name"
                      size="lg"
                    />
                    {errors.adoProject && (
                      <FormHelperText color="red.500">
                        {errors.adoProject.message as string}
                      </FormHelperText>
                    )}
                    <FormHelperText>
                      Enter your Azure DevOps project name (e.g., "myorg/myproject" or "myproject")
                    </FormHelperText>
                  </FormControl>
                
                <HStack spacing={4}>
                  <FormControl isRequired isInvalid={!!errors.areaPath}>
                    <FormLabel>Area Path</FormLabel>
                    <Input 
                      {...register('areaPath', { required: 'Area path is required' })} 
                      placeholder="e.g., Grit, Data Visualization"
                      size="lg"
                    />
                    {errors.areaPath && (
                      <FormHelperText color="red.500">
                        {errors.areaPath.message as string}
                      </FormHelperText>
                    )}
                  </FormControl>
                  
                  <FormControl isRequired isInvalid={!!errors.iterationPath}>
                    <FormLabel>Iteration Path</FormLabel>
                    <Input 
                      {...register('iterationPath', { required: 'Iteration path is required' })} 
                      placeholder="e.g., Sprint 1, Backlog"
                      size="lg"
                    />
                    {errors.iterationPath && (
                      <FormHelperText color="red.500">
                        {errors.iterationPath.message as string}
                      </FormHelperText>
                    )}
                  </FormControl>
                </HStack>
              </VStack>
            </Box>
            
            <Divider />
            
            {/* Submit Button */}
            <Button
              type="submit"
              colorScheme="blue"
              size="lg"
              isLoading={isSubmitting}
              loadingText="Generating Backlog..."
              height="60px"
              fontSize="lg"
            >
              Generate Agile Backlog
            </Button>
          </VStack>
        </form>
        
        <Box bg="blue.50" p={4} borderRadius="md" mt={4}>
          <Text fontSize="sm" color="blue.700">
            <strong>Note:</strong> The Personal Access Token will be loaded from your environment configuration. 
            Ensure your .env file is properly configured with AZURE_DEVOPS_PAT.
          </Text>
        </Box>
      </VStack>
    </Box>
  );
};

export default SimplifiedProjectForm;
