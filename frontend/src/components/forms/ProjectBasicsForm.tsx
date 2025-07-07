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
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
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
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: {
      name: initialData.name || '',
      description: initialData.description || '',
      domain: initialData.domain || '',
      teamSize: initialData.teamSize || 5,
      timeline: initialData.timeline || '3 months',
    }
  });
  
  const teamSize = watch('teamSize');
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
          
          <FormControl>
            <FormLabel>Description</FormLabel>
            <Textarea 
              {...register('description')} 
              placeholder="Brief description of the project"
              size="lg"
              rows={3}
            />
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
          
          <FormControl>
            <FormLabel>Team Size: {teamSize} people</FormLabel>
            <Slider
              defaultValue={teamSize}
              min={1}
              max={20}
              step={1}
              {...register('teamSize')}
              colorScheme="brand"
            >
              <SliderMark value={1} mt='3' ml='-1' fontSize='sm'>
                1
              </SliderMark>
              <SliderMark value={10} mt='3' ml='-2' fontSize='sm'>
                10
              </SliderMark>
              <SliderMark value={20} mt='3' ml='-2' fontSize='sm'>
                20+
              </SliderMark>
              <SliderTrack>
                <SliderFilledTrack />
              </SliderTrack>
              <SliderThumb boxSize={6} />
            </Slider>
          </FormControl>
          
          <FormControl isRequired isInvalid={!!errors.timeline}>
            <FormLabel>Timeline</FormLabel>
            <Select 
              {...register('timeline', { required: 'Timeline is required' })}
              placeholder="Select project timeline"
              size="lg"
            >
              <option value="1 month">1 Month</option>
              <option value="3 months">3 Months</option>
              <option value="6 months">6 Months</option>
              <option value="1 year">1 Year</option>
              <option value="1+ years">More than 1 Year</option>
            </Select>
            {errors.timeline && (
              <FormHelperText color="red.500">
                {errors.timeline.message as string}
              </FormHelperText>
            )}
          </FormControl>
          
          <HStack justify="flex-end" pt={4}>
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
