import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Textarea,
  VStack,
  HStack,
  Input,
  FormHelperText,
  Tag,
  TagLabel,
  TagCloseButton,
  Flex,
  useColorModeValue,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

interface VisionFormProps {
  onNext: (data: any) => void;
  onPrevious?: () => void;
  initialData?: any;
}

const VisionForm: React.FC<VisionFormProps> = ({
  onNext,
  onPrevious,
  initialData = {},
}) => {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
    defaultValues: {
      visionStatement: initialData.visionStatement || '',
      businessObjectives: initialData.businessObjectives || [],
      successMetrics: initialData.successMetrics || [],
      targetAudience: initialData.targetAudience || '',
    }
  });
  
  // State for tag inputs
  const [newObjective, setNewObjective] = React.useState('');
  const [newMetric, setNewMetric] = React.useState('');
  
  // Get values from form
  const businessObjectives = watch('businessObjectives') || [];
  const successMetrics = watch('successMetrics') || [];
  
  // Add new business objective
  const addObjective = () => {
    if (newObjective.trim() !== '') {
      setValue('businessObjectives', [...businessObjectives, newObjective.trim()]);
      setNewObjective('');
    }
  };
  
  // Remove business objective
  const removeObjective = (index: number) => {
    const updatedObjectives = [...businessObjectives];
    updatedObjectives.splice(index, 1);
    setValue('businessObjectives', updatedObjectives);
  };
  
  // Add new success metric
  const addMetric = () => {
    if (newMetric.trim() !== '') {
      setValue('successMetrics', [...successMetrics, newMetric.trim()]);
      setNewMetric('');
    }
  };
  
  // Remove success metric
  const removeMetric = (index: number) => {
    const updatedMetrics = [...successMetrics];
    updatedMetrics.splice(index, 1);
    setValue('successMetrics', updatedMetrics);
  };
  
  const onSubmit = (data: any) => {
    onNext(data);
  };
  
  const bgColor = useColorModeValue('white', 'gray.700');
  
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
          <FormControl isRequired isInvalid={!!errors.visionStatement}>
            <FormLabel>Vision Statement</FormLabel>
            <Textarea 
              {...register('visionStatement', { 
                required: 'Vision statement is required',
                minLength: { value: 20, message: 'Vision statement should be at least 20 characters' } 
              })} 
              placeholder="Our vision is to..."
              size="lg"
              rows={4}
            />
            {errors.visionStatement && (
              <FormHelperText color="red.500">
                {errors.visionStatement.message as string}
              </FormHelperText>
            )}
            <FormHelperText>
              A clear statement of what the project aims to achieve
            </FormHelperText>
          </FormControl>
          
          <FormControl>
            <FormLabel>Business Objectives</FormLabel>
            <HStack mb={2}>
              <Input 
                value={newObjective}
                onChange={(e) => setNewObjective(e.target.value)}
                placeholder="Enter business objective"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addObjective();
                  }
                }}
              />
              <Button onClick={addObjective}>Add</Button>
            </HStack>
            <Flex wrap="wrap" gap={2} mt={2}>
              {businessObjectives.map((objective: string, index: number) => (
                <Tag key={index} size="lg" borderRadius="full" variant="solid" colorScheme="brand">
                  <TagLabel>{objective}</TagLabel>
                  <TagCloseButton onClick={() => removeObjective(index)} />
                </Tag>
              ))}
            </Flex>
          </FormControl>
          
          <FormControl>
            <FormLabel>Success Metrics</FormLabel>
            <HStack mb={2}>
              <Input 
                value={newMetric}
                onChange={(e) => setNewMetric(e.target.value)}
                placeholder="Enter success metric"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addMetric();
                  }
                }}
              />
              <Button onClick={addMetric}>Add</Button>
            </HStack>
            <Flex wrap="wrap" gap={2} mt={2}>
              {successMetrics.map((metric: string, index: number) => (
                <Tag key={index} size="lg" borderRadius="full" variant="solid" colorScheme="green">
                  <TagLabel>{metric}</TagLabel>
                  <TagCloseButton onClick={() => removeMetric(index)} />
                </Tag>
              ))}
            </Flex>
          </FormControl>
          
          <FormControl>
            <FormLabel>Target Audience</FormLabel>
            <Textarea 
              {...register('targetAudience')} 
              placeholder="Describe your target audience..."
              size="lg"
              rows={3}
            />
            <FormHelperText>
              Who will use or benefit from this project
            </FormHelperText>
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

export default VisionForm;
