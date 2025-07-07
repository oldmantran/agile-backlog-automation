import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  VStack,
  HStack,
  Text,
  Divider,
  useColorModeValue,
  Checkbox,
  Select,
  FormHelperText,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

interface AiConfigFormProps {
  onNext: (data: any) => void;
  onPrevious?: () => void;
  initialData?: any;
}

const AiConfigForm: React.FC<AiConfigFormProps> = ({
  onNext,
  onPrevious,
  initialData = {},
}) => {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    defaultValues: {
      modelType: initialData.modelType || 'gpt4o',
      enableAdvancedFeatures: initialData.enableAdvancedFeatures || false,
      enableWorkItemLinking: initialData.enableWorkItemLinking || true,
      enhanceRequirements: initialData.enhanceRequirements || true,
      generateTestCases: initialData.generateTestCases || true,
      generateAcceptanceCriteria: initialData.generateAcceptanceCriteria || true,
      estimateComplexity: initialData.estimateComplexity || true,
      minBacklogItems: initialData.minBacklogItems || 20,
      maxBacklogItems: initialData.maxBacklogItems || 50,
      creativityLevel: initialData.creativityLevel || 'balanced',
      domainSpecificTerms: initialData.domainSpecificTerms || '',
    }
  });
  
  const enableAdvancedFeatures = watch('enableAdvancedFeatures');
  const bgColor = useColorModeValue('white', 'gray.700');
  
  const onSubmit = (data: any) => {
    onNext(data);
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
          <FormControl>
            <FormLabel>AI Model</FormLabel>
            <Select 
              {...register('modelType')} 
              size="lg"
            >
              <option value="gpt4o">GPT-4o (Recommended)</option>
              <option value="gpt35turbo">GPT-3.5 Turbo (Faster)</option>
              <option value="gpt4">GPT-4 (Legacy)</option>
              <option value="phi3">Phi-3 (Local)</option>
            </Select>
            <FormHelperText>
              Select the AI model to use for backlog generation
            </FormHelperText>
          </FormControl>
          
          <FormControl>
            <FormLabel>Content Generation Features</FormLabel>
            <VStack align="start" spacing={3} pl={4}>
              <Checkbox 
                {...register('enableWorkItemLinking')} 
                defaultChecked 
                colorScheme="brand"
              >
                Link work items based on dependencies
              </Checkbox>
              
              <Checkbox 
                {...register('enhanceRequirements')} 
                defaultChecked 
                colorScheme="brand"
              >
                Enhance requirements with additional context
              </Checkbox>
              
              <Checkbox 
                {...register('generateTestCases')} 
                defaultChecked 
                colorScheme="brand"
              >
                Generate test cases for user stories
              </Checkbox>
              
              <Checkbox 
                {...register('generateAcceptanceCriteria')} 
                defaultChecked 
                colorScheme="brand"
              >
                Generate acceptance criteria
              </Checkbox>
              
              <Checkbox 
                {...register('estimateComplexity')} 
                defaultChecked 
                colorScheme="brand"
              >
                Estimate complexity (story points)
              </Checkbox>
            </VStack>
          </FormControl>
          
          <Divider />
          
          <FormControl>
            <FormLabel>Advanced Configuration</FormLabel>
            <Checkbox 
              {...register('enableAdvancedFeatures')} 
              colorScheme="brand"
              mb={4}
            >
              Enable advanced configuration
            </Checkbox>
            
            {enableAdvancedFeatures && (
              <VStack spacing={4} align="stretch" pl={4}>
                <FormControl>
                  <FormLabel>Backlog Size Limits</FormLabel>
                  <HStack spacing={4}>
                    <FormControl>
                      <FormLabel fontSize="sm">Minimum Items</FormLabel>
                      <NumberInput 
                        min={5} 
                        max={100} 
                        defaultValue={20}
                        onChange={(valueString) => setValue('minBacklogItems', parseInt(valueString))}
                      >
                        <NumberInputField {...register('minBacklogItems')} />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Maximum Items</FormLabel>
                      <NumberInput 
                        min={10} 
                        max={200} 
                        defaultValue={50}
                        onChange={(valueString) => setValue('maxBacklogItems', parseInt(valueString))}
                      >
                        <NumberInputField {...register('maxBacklogItems')} />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                    </FormControl>
                  </HStack>
                </FormControl>
                
                <FormControl>
                  <FormLabel>Creativity Level</FormLabel>
                  <Select 
                    {...register('creativityLevel')} 
                    defaultValue="balanced"
                  >
                    <option value="conservative">Conservative (Focus on core requirements)</option>
                    <option value="balanced">Balanced (Recommended)</option>
                    <option value="creative">Creative (Generate more innovative ideas)</option>
                    <option value="highly_creative">Highly Creative (Maximum innovation)</option>
                  </Select>
                </FormControl>
              </VStack>
            )}
          </FormControl>
          
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

export default AiConfigForm;
