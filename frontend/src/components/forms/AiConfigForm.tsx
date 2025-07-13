import React from 'react';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Separator } from '../ui/separator';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { useForm, Controller } from 'react-hook-form';

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
  const { register, handleSubmit, watch, setValue, control, formState: { errors } } = useForm({
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
  
  const onSubmit = (data: any) => {
    onNext(data);
  };
  
  return (
    <div className="bg-card p-6 rounded-lg shadow-md w-full">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="modelType" className="text-foreground">AI Model</Label>
            <Controller
              name="modelType"
              control={control}
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className="h-12">
                    <SelectValue placeholder="Select AI Model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt4o">GPT-4o (Recommended)</SelectItem>
                    <SelectItem value="gpt35turbo">GPT-3.5 Turbo (Faster)</SelectItem>
                    <SelectItem value="gpt4">GPT-4 (Legacy)</SelectItem>
                    <SelectItem value="phi3">Phi-3 (Local)</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <p className="text-sm text-muted-foreground">
              Select the AI model to use for backlog generation
            </p>
          </div>
          
          <div className="space-y-2">
            <Label className="text-foreground">Content Generation Features</Label>
            <div className="space-y-3 pl-4">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="enableWorkItemLinking"
                  {...register('enableWorkItemLinking')} 
                  defaultChecked
                />
                <Label htmlFor="enableWorkItemLinking" className="text-sm font-normal">
                  Link work items based on dependencies
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="enhanceRequirements"
                  {...register('enhanceRequirements')} 
                  defaultChecked
                />
                <Label htmlFor="enhanceRequirements" className="text-sm font-normal">
                  Enhance requirements with additional context
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="generateTestCases"
                  {...register('generateTestCases')} 
                  defaultChecked
                />
                <Label htmlFor="generateTestCases" className="text-sm font-normal">
                  Generate test cases for user stories
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="generateAcceptanceCriteria"
                  {...register('generateAcceptanceCriteria')} 
                  defaultChecked
                />
                <Label htmlFor="generateAcceptanceCriteria" className="text-sm font-normal">
                  Generate acceptance criteria
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="estimateComplexity"
                  {...register('estimateComplexity')} 
                  defaultChecked
                />
                <Label htmlFor="estimateComplexity" className="text-sm font-normal">
                  Estimate complexity (story points)
                </Label>
              </div>
            </div>
          </div>
          
          <Separator />
          
          <div className="space-y-2">
            <Label className="text-foreground">Advanced Configuration</Label>
            <div className="flex items-center space-x-2 mb-4">
              <Checkbox 
                id="enableAdvancedFeatures"
                {...register('enableAdvancedFeatures')}
              />
              <Label htmlFor="enableAdvancedFeatures" className="text-sm font-normal">
                Enable advanced configuration
              </Label>
            </div>
            
            {enableAdvancedFeatures && (
              <div className="space-y-4 pl-4">
                <div className="space-y-2">
                  <Label htmlFor="backlogSizeLimits" className="text-foreground">Backlog Size Limits</Label>
                  <div className="flex space-x-4">
                    <div className="space-y-2">
                      <Label htmlFor="minItems" className="text-sm">Minimum Items</Label>
                      <Controller
                        name="minBacklogItems"
                        control={control}
                        render={({ field }) => (
                          <Input
                            id="minItems"
                            type="number"
                            min={5}
                            value={field.value || 20}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                            className="w-24"
                          />
                        )}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="maxItems" className="text-sm">Maximum Items</Label>
                      <Controller
                        name="maxBacklogItems"
                        control={control}
                        render={({ field }) => (
                          <Input
                            id="maxItems"
                            type="number"
                            min={10}
                            max={200}
                            value={field.value || 50}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                            className="w-24"
                          />
                        )}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="creativityLevel" className="text-foreground">Creativity Level</Label>
                  <Controller
                    name="creativityLevel"
                    control={control}
                    render={({ field }) => (
                      <Select value={field.value || "balanced"} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select creativity level" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="conservative">Conservative (Focus on core requirements)</SelectItem>
                          <SelectItem value="balanced">Balanced (Recommended)</SelectItem>
                          <SelectItem value="creative">Creative (Generate more innovative ideas)</SelectItem>
                          <SelectItem value="highly_creative">Highly Creative (Maximum innovation)</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </div>
            )}
          </div>
          
          <div className="flex justify-between pt-4">
            {onPrevious && (
              <Button 
                onClick={onPrevious}
                size="lg"
                variant="outline"
              >
                Previous
              </Button>
            )}
            <Button 
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

export default AiConfigForm;
