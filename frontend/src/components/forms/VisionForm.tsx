import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
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
  
  return (
    <div className="bg-card p-6 rounded-lg shadow-md w-full">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="visionStatement" className="text-foreground">
              Vision Statement <span className="text-destructive">*</span>
            </Label>
            <Textarea 
              id="visionStatement"
              {...register('visionStatement', { 
                required: 'Vision statement is required',
                minLength: { value: 20, message: 'Vision statement should be at least 20 characters' } 
              })} 
              placeholder="Our vision is to..."
              className="min-h-[100px]"
            />
            {errors.visionStatement && (
              <p className="text-sm text-destructive">
                {errors.visionStatement.message as string}
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              A clear statement of what the project aims to achieve
            </p>
          </div>
          
          <div className="space-y-2">
            <Label className="text-foreground">Business Objectives</Label>
            <div className="flex gap-2 mb-2">
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
              <Button onClick={addObjective} type="button">Add</Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {businessObjectives.map((objective: string, index: number) => (
                <Badge key={index} variant="default" className="bg-primary text-primary-foreground">
                  {objective}
                  <button 
                    type="button"
                    onClick={() => removeObjective(index)}
                    className="ml-2 hover:bg-primary-foreground hover:text-primary rounded-full w-4 h-4 flex items-center justify-center text-xs"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          </div>
          
          <div className="space-y-2">
            <Label className="text-foreground">Success Metrics</Label>
            <div className="flex gap-2 mb-2">
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
              <Button onClick={addMetric} type="button">Add</Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {successMetrics.map((metric: string, index: number) => (
                <Badge key={index} variant="secondary" className="bg-secondary text-secondary-foreground">
                  {metric}
                  <button 
                    type="button"
                    onClick={() => removeMetric(index)}
                    className="ml-2 hover:bg-secondary-foreground hover:text-secondary rounded-full w-4 h-4 flex items-center justify-center text-xs"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="targetAudience" className="text-foreground">Target Audience</Label>
            <Textarea 
              id="targetAudience"
              {...register('targetAudience')} 
              placeholder="Describe your target audience..."
              className="min-h-[75px]"
            />
            <p className="text-sm text-muted-foreground">
              Who will use or benefit from this project
            </p>
          </div>
          
          <div className="flex justify-between pt-4">
            {onPrevious && (
              <Button 
                onClick={onPrevious}
                variant="outline"
                size="lg"
                type="button"
              >
                Previous
              </Button>
            )}
            <Button 
              variant="default"
              size="lg" 
              type="submit"
              className="ml-auto min-w-[150px]"
            >
              Next
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default VisionForm;
