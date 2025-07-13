import React from 'react';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { LoaderIcon, InfoIcon, CheckCircle, XCircle } from 'lucide-react';

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
  
  // Function to toggle token visibility
  const toggleTokenVisibility = () => setShowToken(!showToken);
  
  // Validation function (placeholder - replace with actual API call)
  const validateConnection = async () => {
    setValidating(true);
    // Simulate API call
    setTimeout(() => {
      setValidationResult({
        success: true,
        message: 'Connection validated successfully!'
      });
      setAvailableProjects(['Project 1', 'Project 2', 'Backlog Automation']);
      setValidating(false);
    }, 2000);
  };

  const loadAreaPaths = async () => {
    // Placeholder for loading area paths
    setAvailableAreaPaths(['Area\\Path1', 'Area\\Path2']);
  };

  const loadIterations = async () => {
    // Placeholder for loading iterations
    setAvailableIterations(['Sprint 1', 'Sprint 2']);
  };

  const onSubmit = (data: any) => {
    if (useExistingConfig) {
      const envConfig = {
        organizationUrl: 'ENVIRONMENT_CONFIG',
        personalAccessToken: 'ENVIRONMENT_CONFIG',
        project: 'Backlog Automation',
        areaPath: '',
        iterationPath: '',
        useExistingConfig: true
      };
      onNext(envConfig);
    } else {
      if (!data.areaPath || !data.iterationPath) {
        alert('Both Area Path and Iteration Path are required.');
        return;
      }
      onNext(data);
    }
  };
  
  return (
    <Card className="w-full max-w-2xl mx-auto shadow-lg border-cyan-500/20">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Switch for existing config */}
          <div className="flex items-center space-x-2">
            <Switch 
              id="use-existing"
              {...register('useExistingConfig')}
            />
            <Label htmlFor="use-existing" className="text-cyan-100">
              Use existing Azure DevOps configuration
            </Label>
          </div>
          
          {useExistingConfig ? (
            <Alert className="border-cyan-500/30 bg-cyan-950/30">
              <InfoIcon className="h-4 w-4" />
              <AlertDescription className="text-cyan-100">
                Using existing Azure DevOps configuration from your settings.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-6">
              {/* Organization URL */}
              <div className="space-y-2">
                <Label htmlFor="organizationUrl" className="text-cyan-100">
                  Azure DevOps Organization URL *
                </Label>
                <Input 
                  id="organizationUrl"
                  {...register('organizationUrl', { 
                    required: 'Organization URL is required',
                    pattern: {
                      value: /^https:\/\/dev\.azure\.com\/[a-zA-Z0-9_-]+$/,
                      message: 'Must be a valid Azure DevOps URL (https://dev.azure.com/organization)'
                    }
                  })} 
                  placeholder="https://dev.azure.com/organization"
                  className="bg-slate-800/50 border-cyan-500/30 text-cyan-100 placeholder:text-cyan-400/50"
                />
                {errors.organizationUrl && (
                  <p className="text-red-400 text-sm">
                    {errors.organizationUrl.message as string}
                  </p>
                )}
              </div>
              
              {/* Personal Access Token */}
              <div className="space-y-2">
                <Label htmlFor="personalAccessToken" className="text-cyan-100">
                  Personal Access Token (PAT) *
                </Label>
                <div className="relative">
                  <Input 
                    id="personalAccessToken"
                    {...register('personalAccessToken', { 
                      required: 'Personal Access Token is required' 
                    })} 
                    type={showToken ? 'text' : 'password'}
                    placeholder="Personal Access Token"
                    className="bg-slate-800/50 border-cyan-500/30 text-cyan-100 placeholder:text-cyan-400/50 pr-12"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 text-cyan-400 hover:text-cyan-300"
                    onClick={toggleTokenVisibility}
                  >
                    {showToken ? <FiEyeOff /> : <FiEye />}
                  </Button>
                </div>
                {errors.personalAccessToken && (
                  <p className="text-red-400 text-sm">
                    {errors.personalAccessToken.message as string}
                  </p>
                )}
                <p className="text-cyan-400/70 text-sm">
                  Create a PAT with 'Work Items (Read & Write)' scope
                </p>
              </div>
              
              {/* Validate Connection Button */}
              <Button 
                type="button"
                onClick={validateConnection}
                disabled={validating}
                className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                {validating ? (
                  <>
                    <LoaderIcon className="mr-2 h-4 w-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  'Validate Connection'
                )}
              </Button>
              
              {/* Validation Result */}
              {validationResult.message && (
                <Alert className={`border-2 ${
                  validationResult.success 
                    ? 'border-green-500/30 bg-green-950/30' 
                    : 'border-red-500/30 bg-red-950/30'
                }`}>
                  {validationResult.success ? (
                    <CheckCircle className="h-4 w-4 text-green-400" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-400" />
                  )}
                  <AlertDescription className={validationResult.success ? 'text-green-100' : 'text-red-100'}>
                    {validationResult.message}
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Project field - only show after successful validation */}
              {validationResult.success && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="project" className="text-cyan-100">
                      Project *
                    </Label>
                    <Input 
                      id="project"
                      {...register('project', { 
                        required: 'Project is required' 
                      })} 
                      list="projects"
                      placeholder="Select or enter project name"
                      className="bg-slate-800/50 border-cyan-500/30 text-cyan-100 placeholder:text-cyan-400/50"
                    />
                    <datalist id="projects">
                      {availableProjects.map((project, idx) => (
                        <option key={idx} value={project} />
                      ))}
                    </datalist>
                    {errors.project && (
                      <p className="text-red-400 text-sm">
                        {errors.project.message as string}
                      </p>
                    )}
                  </div>
                  
                  {/* Area Path */}
                  <div className="space-y-2">
                    <Label htmlFor="areaPath" className="text-cyan-100">
                      Area Path *
                    </Label>
                    <Input 
                      id="areaPath"
                      {...register('areaPath', { 
                        required: 'Area Path is required'
                      })} 
                      list="areaPaths"
                      placeholder="Select or enter area path"
                      className="bg-slate-800/50 border-cyan-500/30 text-cyan-100 placeholder:text-cyan-400/50"
                      onFocus={loadAreaPaths}
                    />
                    <datalist id="areaPaths">
                      {availableAreaPaths.map((path, idx) => (
                        <option key={idx} value={path} />
                      ))}
                    </datalist>
                    {errors.areaPath && (
                      <p className="text-red-400 text-sm">
                        {errors.areaPath.message as string}
                      </p>
                    )}
                  </div>
                  
                  {/* Iteration Path */}
                  <div className="space-y-2">
                    <Label htmlFor="iterationPath" className="text-cyan-100">
                      Iteration Path *
                    </Label>
                    <Input 
                      id="iterationPath"
                      {...register('iterationPath', { 
                        required: 'Iteration Path is required'
                      })} 
                      list="iterations"
                      placeholder="Select or enter iteration path"
                      className="bg-slate-800/50 border-cyan-500/30 text-cyan-100 placeholder:text-cyan-400/50"
                      onFocus={loadIterations}
                    />
                    <datalist id="iterations">
                      {availableIterations.map((iteration, idx) => (
                        <option key={idx} value={iteration} />
                      ))}
                    </datalist>
                    {errors.iterationPath && (
                      <p className="text-red-400 text-sm">
                        {errors.iterationPath.message as string}
                      </p>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
          
          {/* Form buttons */}
          <div className="flex justify-between pt-6">
            {onPrevious && (
              <Button
                type="button"
                variant="outline"
                onClick={onPrevious}
                className="border-cyan-500/30 text-cyan-100 hover:bg-cyan-500/10"
              >
                Previous
              </Button>
            )}
            <Button
              type="submit"
              className="bg-cyan-600 hover:bg-cyan-700 text-white ml-auto"
            >
              Next
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default AzureSetupForm;

export {};
