import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Textarea,
  VStack,
  HStack,
  FormHelperText,
  useColorModeValue,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { domains } from '../../utils/constants/domains';

interface ProjectBasicsFormProps {
  onNext: (data: any) => void;
  onPrevious?: () => void;
  initialData?: any;
}

const ProjectBasicsForm: React.FC<ProjectBasicsFormProps> = ({
  onNext,
  initialData = {},
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: initialData.name || '',
      description: initialData.description || '',
      domain: initialData.domain || '',
    }
  });
  
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
        <VStack spacing={4} align="stretch">
          <FormControl isRequired isInvalid={!!errors.name}>
            <FormLabel>Project Name</FormLabel>
            <Input 
              {...register('name', { 
                required: 'Project name is required',
                minLength: { value: 3, message: 'Name must be at least 3 characters' } 
              })} 
              placeholder="Enter project name"
              size="lg"
            />
            {errors.name && (
              <FormHelperText color="red.500">
                {errors.name.message as string}
              </FormHelperText>
            )}
          </FormControl>
          
          <FormControl isRequired isInvalid={!!errors.description}>
            <FormLabel>Description</FormLabel>
            <Textarea 
              {...register('description', { required: 'Description is required' })} 
              placeholder="Brief description of the project"
              size="lg"
              rows={3}
            />
            {errors.description && (
              <FormHelperText color="red.500">
                {errors.description.message as string}
              </FormHelperText>
            )}
          </FormControl>
          
          <FormControl isRequired isInvalid={!!errors.domain}>
            <FormLabel>Domain</FormLabel>
            <Select 
              {...register('domain', { required: 'Domain is required' })}
              placeholder="Select domain"
              size="lg"
            >
              {domains.map(domain => (
                <option key={domain.value} value={domain.value}>
                  {domain.label}
                </option>
              ))}
            </Select>
            {errors.domain && (
              <FormHelperText color="red.500">
                {errors.domain.message as string}
              </FormHelperText>
            )}
          </FormControl>
          
          <HStack mt={8} justify="flex-end">
            <Button 
              colorScheme="brand" 
              size="lg" 
              type="submit"
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

export default ProjectBasicsForm;
