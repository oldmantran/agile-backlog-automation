import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  HStack,
  FormHelperText,
  useColorModeValue,
  Text,
  InputGroup,
  InputRightElement,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  Switch,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';

interface AzureSetupFormProps {
  onNext: (data: any) => void;
  onPrevious?: () => void;
  initialData?: any;
}

const AzureSetupForm: React.FC<AzureSetupFormProps> = ({
  onNext,
  onPrevious,
  initialData = {},
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm({
    defaultValues: {
      organizationUrl: initialData.organizationUrl || '',
      personalAccessToken: initialData.personalAccessToken || '',
      project: initialData.project || '',
      areaPath: initialData.areaPath || '',
      iterationPath: initialData.iterationPath || '',
      useExistingConfig: initialData.useExistingConfig || false,
    }
  });
  
  const [showToken, setShowToken] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    success?: boolean;
    message?: string;
  }>({});
  const [availableProjects, setAvailableProjects] = useState<string[]>([]);
  const [availableAreaPaths, setAvailableAreaPaths] = useState<string[]>([]);
  const [availableIterations, setAvailableIterations] = useState<string[]>([]);
  
  const useExistingConfig = watch('useExistingConfig');
  const bgColor = useColorModeValue('white', 'gray.700');
  
  // Function to toggle token visibility
  const toggleTokenVisibility = () => setShowToken(!showToken);
  
  // Function to validate Azure DevOps connection
  const validateConnection = async () => {
    try {
      setValidating(true);
      setValidationResult({});
      
      // This would be an actual API call in production
      // For now just simulating a call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate success
      setValidationResult({
        success: true,
        message: 'Connection successful!'
      });
      
      // Mock data
      setAvailableProjects(['Project1', 'Project2', 'Project3']);
      
    } catch (error) {
      setValidationResult({
        success: false,
        message: 'Failed to connect to Azure DevOps'
      });
    } finally {
      setValidating(false);
    }
  };
  
  // Function to load area paths
  const loadAreaPaths = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800));
    setAvailableAreaPaths(['Area1', 'Area1/SubArea1', 'Area2', 'Area3/SubArea1/SubArea2']);
  };
  
  // Function to load iterations
  const loadIterations = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800));
    setAvailableIterations(['Iteration1', 'Iteration2', 'Iteration2/Sprint1', 'Iteration2/Sprint2']);
  };
  
  const onSubmit = (data: any) => {
    // If using existing config, populate with environment data
    if (data.useExistingConfig) {
      const envConfig = {
        organizationUrl: 'https://dev.azure.com/c4workx', // From .env AZURE_DEVOPS_ORG
        personalAccessToken: 'ENVIRONMENT_CONFIG', // Indicate it's from environment
        project: 'Backlog Automation', // From .env AZURE_DEVOPS_PROJECT
        areaPath: '', // Use default
        iterationPath: '', // Use default
        useExistingConfig: true
      };
      onNext(envConfig);
    } else {
      onNext(data);
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
      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={6} align="stretch">
          <FormControl display="flex" alignItems="center">
            <FormLabel htmlFor="use-existing" mb="0">
              Use existing Azure DevOps configuration
            </FormLabel>
            <Switch 
              id="use-existing" 
              colorScheme="brand"
              {...register('useExistingConfig')}
            />
          </FormControl>
          
          {useExistingConfig ? (
            <Alert status="info">
              <AlertIcon />
              <AlertDescription>
                Using existing Azure DevOps configuration from your settings.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <FormControl isRequired isInvalid={!!errors.organizationUrl}>
                <FormLabel>Azure DevOps Organization URL</FormLabel>
                <Input 
                  {...register('organizationUrl', { 
                    required: 'Organization URL is required',
                    pattern: {
                      value: /^https:\/\/dev\.azure\.com\/[a-zA-Z0-9_-]+$/,
                      message: 'Must be a valid Azure DevOps URL (https://dev.azure.com/organization)'
                    }
                  })} 
                  placeholder="https://dev.azure.com/organization"
                  size="lg"
                />
                {errors.organizationUrl && (
                  <FormHelperText color="red.500">
                    {errors.organizationUrl.message as string}
                  </FormHelperText>
                )}
              </FormControl>
              
              <FormControl isRequired isInvalid={!!errors.personalAccessToken}>
                <FormLabel>Personal Access Token (PAT)</FormLabel>
                <InputGroup size="lg">
                  <Input 
                    {...register('personalAccessToken', { 
                      required: 'Personal Access Token is required' 
                    })} 
                    type={showToken ? 'text' : 'password'}
                    placeholder="Personal Access Token"
                  />
                  <InputRightElement width="4.5rem">
                    <Button h="1.75rem" size="sm" onClick={toggleTokenVisibility}>
                      {showToken ? <FiEyeOff /> : <FiEye />}
                    </Button>
                  </InputRightElement>
                </InputGroup>
                {errors.personalAccessToken && (
                  <FormHelperText color="red.500">
                    {errors.personalAccessToken.message as string}
                  </FormHelperText>
                )}
                <FormHelperText>
                  Create a PAT with 'Work Items (Read & Write)' scope
                </FormHelperText>
              </FormControl>
              
              <Button 
                onClick={validateConnection}
                colorScheme="blue"
                isLoading={validating}
                loadingText="Validating..."
              >
                Validate Connection
              </Button>
              
              {validationResult.message && (
                <Alert 
                  status={validationResult.success ? 'success' : 'error'}
                  borderRadius="md"
                >
                  <AlertIcon />
                  <AlertDescription>
                    {validationResult.message}
                  </AlertDescription>
                </Alert>
              )}
              
              {validationResult.success && (
                <>
                  <FormControl isRequired isInvalid={!!errors.project}>
                    <FormLabel>Project</FormLabel>
                    <Input 
                      {...register('project', { 
                        required: 'Project is required' 
                      })} 
                      list="projects"
                      placeholder="Select or enter project name"
                      size="lg"
                    />
                    <datalist id="projects">
                      {availableProjects.map((project, idx) => (
                        <option key={idx} value={project} />
                      ))}
                    </datalist>
                    {errors.project && (
                      <FormHelperText color="red.500">
                        {errors.project.message as string}
                      </FormHelperText>
                    )}
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Area Path</FormLabel>
                    <Input 
                      {...register('areaPath')} 
                      list="areaPaths"
                      placeholder="Select or enter area path"
                      size="lg"
                      onFocus={loadAreaPaths}
                    />
                    <datalist id="areaPaths">
                      {availableAreaPaths.map((path, idx) => (
                        <option key={idx} value={path} />
                      ))}
                    </datalist>
                    <FormHelperText>
                      Leave empty to use the root area
                    </FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Iteration Path</FormLabel>
                    <Input 
                      {...register('iterationPath')} 
                      list="iterations"
                      placeholder="Select or enter iteration path"
                      size="lg"
                      onFocus={loadIterations}
                    />
                    <datalist id="iterations">
                      {availableIterations.map((iteration, idx) => (
                        <option key={idx} value={iteration} />
                      ))}
                    </datalist>
                    <FormHelperText>
                      Leave empty to use the current iteration
                    </FormHelperText>
                  </FormControl>
                </>
              )}
            </>
          )}
          
          <HStack justify="space-between" pt={4}>
            {onPrevious && (
              <Button 
                onClick={onPrevious}
                size="lg"
              >
                Previous
              </Button>
            )}
            <Button 
              colorScheme="brand" 
              size="lg" 
              type="submit"
              ml="auto"
              minW="150px"
            >
              Next
            </Button>
          </HStack>
        </VStack>
      </form>
    </Box>
  );
};

export default AzureSetupForm;
