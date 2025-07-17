import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Separator } from '../ui/separator';
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
    }  });

  const onFormSubmit = (data: any) => {
    console.log('🔍 Form submitted with data:', data);
    
    // Transform data to match backend expectations
    // Extract organization and project from input (handles both "org/project" and "project" formats)
    const projectParts = data.adoProject.includes('/') ? data.adoProject.split('/') : [data.adoProject.split('.')[0], data.adoProject];
    const organization = projectParts[0];
    const project = projectParts[1] || projectParts[0];
    
    console.log('🔍 Extracted organization:', organization);
    console.log('🔍 Extracted project:', project);
    
    const projectData = {
      basics: {
        name: project, // Use the Azure DevOps project name as the project name
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
    
    console.log('🔍 Calling onSubmit with projectData:', projectData);
    onSubmit(projectData);
  };
  
  return (
    <div className="bg-card p-8 rounded-xl shadow-lg w-full max-w-3xl mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-2">
            Create Agile Backlog
          </h2>
          <p className="text-muted-foreground">
            Enter your product vision and Azure DevOps details to generate a comprehensive backlog
          </p>
        </div>
        
        <Separator />
        
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className="space-y-6">
            {/* Vision Statement - The core input */}
            <div className="space-y-2">
              <Label htmlFor="visionStatement" className="text-lg font-semibold text-foreground">
                Product Vision & Requirements <span className="text-destructive">*</span>
              </Label>
              <Textarea 
                id="visionStatement"
                {...register('visionStatement', { 
                  required: 'Product vision is required',
                  minLength: { value: 50, message: 'Vision must be at least 50 characters' }
                })} 
                placeholder="Describe your product vision, including goals, objectives, target audience, success metrics, and key features. Be as comprehensive as possible - this will drive the entire backlog generation.

Example: Create a comprehensive ride-sharing platform that connects drivers and passengers with real-time matching, secure payments, and intelligent routing. Target urban commuters and part-time drivers seeking flexible income. Success measured by: 50K+ active users in 6 months, 90%+ ride completion rate, $2M+ annual revenue. Key features include driver background checks, real-time GPS tracking, in-app payments, surge pricing, and customer ratings."
                className="min-h-[200px] resize-y"
              />
              {errors.visionStatement && (
                <p className="text-sm text-destructive">
                  {errors.visionStatement.message as string}
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                Include your vision, goals, target audience, success metrics, and key requirements. The AI will extract objectives, metrics, and target audience from this comprehensive description.
              </p>
            </div>
            
            <Separator />
            
            {/* Azure DevOps Configuration */}
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Azure DevOps Configuration
              </h3>
              
              <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="adoProject">
                      Azure DevOps Project <span className="text-destructive">*</span>
                    </Label>
                    <Input 
                      id="adoProject"
                      {...register('adoProject', { 
                        required: 'Azure DevOps project is required'
                      })} 
                      placeholder="organization/project or project-name"
                      className="h-12"
                    />
                    {errors.adoProject && (
                      <p className="text-sm text-destructive">
                        {errors.adoProject.message as string}
                      </p>
                    )}
                    <p className="text-sm text-muted-foreground">
                      Enter your Azure DevOps project name (e.g., "myorg/myproject" or "myproject")
                    </p>
                  </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="areaPath">
                      Area Path <span className="text-destructive">*</span>
                    </Label>
                    <Input 
                      id="areaPath"
                      {...register('areaPath', { required: 'Area path is required' })} 
                      placeholder="e.g., Grit, Data Visualization"
                      className="h-12"
                    />
                    {errors.areaPath && (
                      <p className="text-sm text-destructive">
                        {errors.areaPath.message as string}
                      </p>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="iterationPath">
                      Iteration Path <span className="text-destructive">*</span>
                    </Label>
                    <Input 
                      id="iterationPath"
                      {...register('iterationPath', { required: 'Iteration path is required' })} 
                      placeholder="e.g., Sprint 1, Backlog"
                      className="h-12"
                    />
                    {errors.iterationPath && (
                      <p className="text-sm text-destructive">
                        {errors.iterationPath.message as string}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <Separator />
            
            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full h-15 text-lg"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Generating Backlog..." : "Generate Agile Backlog"}
            </Button>
          </div>
        </form>
        
        <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-md mt-4">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>Note:</strong> The Personal Access Token will be loaded from your environment configuration. 
            Ensure your .env file is properly configured with AZURE_DEVOPS_PAT.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SimplifiedProjectForm;
