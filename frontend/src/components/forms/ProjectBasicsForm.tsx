import React from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Card, CardContent } from '../ui/card';
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
  const { register, handleSubmit, formState: { errors }, setValue, watch } = useForm({
    defaultValues: {
      name: initialData.name || '',
      description: initialData.description || '',
      domain: initialData.domain || '',
    }
  });
  
  const watchedDomain = watch('domain');
  
  const onSubmit = (data: any) => {
    onNext(data);
  };
  
  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Project Name *
            </label>
            <Input 
              id="name"
              {...register('name', { 
                required: 'Project name is required',
                minLength: { value: 3, message: 'Name must be at least 3 characters' } 
              })} 
              placeholder="Enter project name"
              className={errors.name ? 'border-destructive' : ''}
            />
            {errors.name && (
              <p className="text-sm text-destructive">
                {errors.name.message as string}
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Description *
            </label>
            <Textarea 
              id="description"
              {...register('description', { required: 'Description is required' })} 
              placeholder="Brief description of the project"
              rows={3}
              className={errors.description ? 'border-destructive' : ''}
            />
            {errors.description && (
              <p className="text-sm text-destructive">
                {errors.description.message as string}
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <label htmlFor="domain" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Domain *
            </label>
            <Select onValueChange={(value) => setValue('domain', value)} value={watchedDomain}>
              <SelectTrigger className={errors.domain ? 'border-destructive' : ''}>
                <SelectValue placeholder="Select domain" />
              </SelectTrigger>
              <SelectContent>
                {domains.map(domain => (
                  <SelectItem key={domain.value} value={domain.value}>
                    {domain.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.domain && (
              <p className="text-sm text-destructive">
                {errors.domain.message as string}
              </p>
            )}
          </div>
          
          <div className="flex justify-end mt-8">
            <Button 
              type="submit"
              className="min-w-[150px]"
            >
              Next
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default ProjectBasicsForm;
