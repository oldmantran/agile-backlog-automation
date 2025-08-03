import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { useForm, Controller } from 'react-hook-form';
import { FiGlobe, FiInfo, FiCheck, FiX, FiPlus } from 'react-icons/fi';

interface Domain {
  id: number;
  domain_key: string;
  display_name: string;
  description: string;
  is_active: boolean;
}

interface DomainSelection {
  domain_id: number;
  domain_key: string;
  display_name: string;
  is_primary: boolean;
  weight: number;
}

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
  const { register, handleSubmit, control, watch, setValue, formState: { errors } } = useForm({
    defaultValues: {
      visionStatement: initialData.visionStatement || '',
      adoProject: initialData.adoProject || '',
      areaPath: initialData.areaPath || '',
      iterationPath: initialData.iterationPath || '',
      selectedDomains: initialData.selectedDomains || [],
      useAiDetection: initialData.useAiDetection !== false, // Default to true
      includeTestArtifacts: initialData.includeTestArtifacts === true, // Default to false
    }
  });

  // Domain management state
  const [availableDomains, setAvailableDomains] = useState<Domain[]>([]);
  const [detectedDomain, setDetectedDomain] = useState<string | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  
  // Watch for vision statement changes to trigger AI detection
  const visionStatement = watch('visionStatement');
  const useAiDetection = watch('useAiDetection');
  const selectedDomains = watch('selectedDomains');
  const includeTestArtifacts = watch('includeTestArtifacts');

  // Load available domains on component mount
  useEffect(() => {
    const loadDomains = async () => {
      try {
        const response = await fetch('/api/domains');
        if (response.ok) {
          const domains = await response.json();
          setAvailableDomains(domains);
        } else {
          console.warn('Domains API failed, will show loading state');
          // Don't set fallback domains immediately, let the loading state persist
          // The user will need to restart the backend for the full domain list
        }
      } catch (error) {
        console.error('Failed to load domains:', error);
        // Show minimal fallback to prevent completely broken UI
        const minimalFallback = [
          { id: 1, domain_key: 'technology', display_name: 'Technology', description: 'Software development and technology projects', is_active: true },
          { id: 2, domain_key: 'healthcare', display_name: 'Healthcare', description: 'Healthcare and medical technology', is_active: true },
          { id: 3, domain_key: 'finance', display_name: 'Finance', description: 'Financial services and fintech', is_active: true }
        ];
        setAvailableDomains(minimalFallback);
      }
    };
    loadDomains();
  }, []);

  // AI domain detection when vision statement changes
  useEffect(() => {
    if (visionStatement && visionStatement.length > 50 && useAiDetection) {
      const detectDomain = async () => {
        setIsDetecting(true);
        try {
          const response = await fetch('/api/domains/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: visionStatement })
          });
          if (response.ok) {
            const result = await response.json();
            setDetectedDomain(result.domain);
          }
        } catch (error) {
          console.error('Domain detection failed:', error);
        } finally {
          setIsDetecting(false);
        }
      };
      
      const timeoutId = setTimeout(detectDomain, 1000); // Debounce
      return () => clearTimeout(timeoutId);
    }
  }, [visionStatement, useAiDetection]);

  const handleDomainSelection = (domainKey: string, isPrimary: boolean = false) => {
    const domain = availableDomains.find(d => d.domain_key === domainKey);
    if (!domain) return;

    const currentSelections = selectedDomains || [];
    const existingIndex = currentSelections.findIndex((s: DomainSelection) => s.domain_key === domainKey);
    
    let newSelections;
    if (existingIndex >= 0) {
      // Update existing selection
      newSelections = currentSelections.map((s: DomainSelection, index: number) => 
        index === existingIndex 
          ? { ...s, is_primary: isPrimary, weight: isPrimary ? 1.0 : 0.5 }
          : { ...s, is_primary: false } // Only one primary allowed
      );
    } else {
      // Add new selection
      newSelections = [
        ...currentSelections.map((s: DomainSelection) => ({ ...s, is_primary: false })),
        {
          domain_id: domain.id,
          domain_key: domain.domain_key,
          display_name: domain.display_name,
          is_primary: isPrimary,
          weight: isPrimary ? 1.0 : 0.5
        }
      ];
    }
    
    // Limit to 3 domains maximum
    if (newSelections.length > 3) {
      newSelections = newSelections.slice(0, 3);
    }
    
    return newSelections;
  };

  const removeDomainSelection = (domainKey: string) => {
    const currentSelections = selectedDomains || [];
    return currentSelections.filter((s: DomainSelection) => s.domain_key !== domainKey);
  };

  const onFormSubmit = (data: any) => {
    console.log('🔍 Form submitted with data:', data);
    
    // Transform data to match backend expectations
    const projectParts = data.adoProject.includes('/') ? data.adoProject.split('/') : [data.adoProject.split('.')[0], data.adoProject];
    const organization = projectParts[0];
    const project = projectParts[1] || projectParts[0];
    
    // Determine final domain selection strategy
    let finalDomainStrategy;
    if (!data.useAiDetection || (data.selectedDomains && data.selectedDomains.length > 0)) {
      // User override or manual selection
      finalDomainStrategy = {
        strategy: 'manual',
        domains: data.selectedDomains || [],
        ai_detection_disabled: !data.useAiDetection
      };
    } else {
      // AI detection
      finalDomainStrategy = {
        strategy: 'ai_detection',
        detected_domain: detectedDomain,
        fallback_domain: 'technology' // Default fallback
      };
    }
    
    const projectData = {
      basics: {
        name: project,
        description: data.visionStatement.substring(0, 200) + "...",
        domain: "software_development" // Legacy field
      },
      vision: {
        visionStatement: data.visionStatement,
        businessObjectives: ["TBD"],
        successMetrics: ["TBD"],
        targetAudience: "end users"
      },
      azureConfig: {
        organizationUrl: `https://dev.azure.com/${organization}`,
        personalAccessToken: "",
        project: project,
        areaPath: data.areaPath,
        iterationPath: data.iterationPath
      },
      domainStrategy: finalDomainStrategy, // New domain configuration
      includeTestArtifacts: data.includeTestArtifacts // QA testing option
    };
    
    console.log('🔍 Calling onSubmit with enhanced projectData:', projectData);
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
            
            {/* Domain Selection Section */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <FiGlobe className="w-6 h-6 text-primary" />
                <h3 className="text-lg font-semibold">Domain & Industry Focus</h3>
              </div>
              
              {/* AI Detection Toggle */}
              <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50">
                <div>
                  <p className="font-medium">Enable AI Domain Detection</p>
                  <p className="text-sm text-muted-foreground">
                    Automatically detect industry domain from your vision statement
                  </p>
                </div>
                <Controller
                  name="useAiDetection"
                  control={control}
                  render={({ field }) => (
                    <Button
                      type="button"
                      variant={field.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => {
                        const newValue = !field.value;
                        field.onChange(newValue);
                        // Clear manual domain selections when enabling AI detection
                        if (newValue) {
                          setValue('selectedDomains', []);
                        }
                      }}
                    >
                      {field.value ? <FiCheck className="w-4 h-4 mr-2" /> : <FiX className="w-4 h-4 mr-2" />}
                      {field.value ? 'Enabled' : 'Disabled'}
                    </Button>
                  )}
                />
              </div>
              
              {/* AI Detection Results */}
              {useAiDetection && (
                <div className="space-y-3">
                  {isDetecting && (
                    <Alert>
                      <FiInfo className="w-4 h-4" />
                      <AlertDescription>
                        Analyzing your vision statement to detect industry domain...
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {detectedDomain && !isDetecting && (
                    <Alert className="border-green-500/50 bg-green-500/10">
                      <FiCheck className="w-4 h-4 text-green-500" />
                      <AlertDescription className="text-green-700 dark:text-green-300">
                        <strong>AI Detected Domain:</strong> {availableDomains.find(d => d.domain_key === detectedDomain)?.display_name || detectedDomain}
                        <br />
                        <span className="text-sm opacity-80">
                          The AI will use industry-specific patterns and terminology for this domain.
                        </span>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
              
              {/* Manual Domain Selection */}
              {!useAiDetection && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="font-medium">Manual Domain Selection</Label>
                    <div className="text-xs text-muted-foreground">
                      AI Detection Disabled - Manual Selection Active
                    </div>
                  </div>
                  
                  <div className="space-y-4 p-4 rounded-lg border border-border bg-card">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                        <FiInfo className="w-4 h-4" />
                        <span>Select up to 3 domains. Click to add/remove. First selected becomes primary.</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {selectedDomains.length}/3 selected
                      </div>
                    </div>
                    
                    {/* Domain Grid Selection */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-60 overflow-y-auto">
                      {availableDomains.map(domain => {
                        const isSelected = selectedDomains.some((s: DomainSelection) => s.domain_key === domain.domain_key);
                        const selectedDomain = selectedDomains.find((s: DomainSelection) => s.domain_key === domain.domain_key);
                        const isPrimary = selectedDomain?.is_primary || false;
                        
                        return (
                          <div
                            key={domain.domain_key}
                            onClick={() => {
                              if (isSelected) {
                                // Remove domain
                                const newSelections = removeDomainSelection(domain.domain_key);
                                setValue('selectedDomains', newSelections);
                              } else if (selectedDomains.length < 3) {
                                // Add domain
                                const newSelections = handleDomainSelection(domain.domain_key, selectedDomains.length === 0);
                                if (newSelections) {
                                  setValue('selectedDomains', newSelections);
                                }
                              }
                            }}
                            className={`
                              relative p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:scale-105
                              ${isSelected 
                                ? isPrimary 
                                  ? 'border-primary bg-primary/20 shadow-lg' 
                                  : 'border-secondary bg-secondary/20 shadow-md'
                                : 'border-border bg-background hover:border-muted-foreground'
                              }
                              ${selectedDomains.length >= 3 && !isSelected ? 'opacity-50 cursor-not-allowed' : ''}
                            `}
                          >
                            <div className="text-sm font-medium text-foreground truncate">
                              {domain.display_name}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {domain.description}
                            </div>
                            
                            {/* Selection indicator */}
                            {isSelected && (
                              <div className={`absolute top-1 right-1 w-4 h-4 rounded-full flex items-center justify-center text-xs font-bold
                                ${isPrimary ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}
                              `}>
                                {isPrimary ? '1' : '2'}
                              </div>
                            )}
                            
                            {/* Add/Remove icon */}
                            <div className="absolute bottom-1 right-1">
                              {isSelected ? (
                                <FiX className="w-3 h-3 text-destructive" />
                              ) : (
                                selectedDomains.length < 3 && <FiPlus className="w-3 h-3 text-muted-foreground" />
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    {/* Selected Domains Display */}
                    {selectedDomains && selectedDomains.length > 0 && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium">Selected Domains:</Label>
                        <div className="flex flex-wrap gap-2">
                          {selectedDomains.map((selection: DomainSelection, index: number) => (
                            <Badge 
                              key={selection.domain_key} 
                              variant={selection.is_primary ? "default" : "secondary"}
                              className="flex items-center space-x-2 px-3 py-1"
                            >
                              <span>{selection.display_name}</span>
                              {selection.is_primary && (
                                <span className="text-xs bg-primary/20 px-1 rounded">PRIMARY</span>
                              )}
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="h-auto p-0 ml-2 hover:bg-transparent"
                                onClick={() => {
                                  const newSelections = removeDomainSelection(selection.domain_key);
                                  setValue('selectedDomains', newSelections);
                                }}
                              >
                                <FiX className="w-3 h-3" />
                              </Button>
                            </Badge>
                          ))}
                        </div>
                        
                        {selectedDomains.length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            The primary domain will have the strongest influence on backlog generation. 
                            Secondary domains provide additional context.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <Separator />
            
            {/* Testing & QA Options */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <FiInfo className="w-6 h-6 text-primary" />
                <h3 className="text-lg font-semibold">Backlog Generation Options</h3>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50">
                <div className="space-y-1">
                  <p className="font-medium">Include Test Artifacts</p>
                  <p className="text-sm text-muted-foreground">
                    Generate test plans, test suites, and test cases along with work items. 
                    Disable to generate work items only and add testing later.
                  </p>
                </div>
                <Controller
                  name="includeTestArtifacts"
                  control={control}
                  render={({ field }) => (
                    <Button
                      type="button"
                      variant={field.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => field.onChange(!field.value)}
                      className="min-w-24"
                    >
                      {field.value ? (
                        <>
                          <FiCheck className="w-4 h-4 mr-2" />
                          Enabled
                        </>
                      ) : (
                        <>
                          <FiX className="w-4 h-4 mr-2" />
                          Disabled
                        </>
                      )}
                    </Button>
                  )}
                />
              </div>
              
              {/* Processing Time Info */}
              <div className={`p-3 rounded-lg border ${
                includeTestArtifacts 
                  ? 'border-yellow-500/30 bg-yellow-500/10' 
                  : 'border-green-500/30 bg-green-500/10'
              }`}>
                <div className={`flex items-center space-x-2 text-sm ${
                  includeTestArtifacts ? 'text-yellow-700 dark:text-yellow-300' : 'text-green-700 dark:text-green-300'
                }`}>
                  <FiInfo className="w-4 h-4" />
                  <span>
                    <strong>Processing Time:</strong> {includeTestArtifacts 
                      ? 'Full generation with testing (~45-90 minutes for comprehensive backlogs)'
                      : 'Work items only (~15-30 minutes, add testing later as needed)'
                    }
                  </span>
                </div>
              </div>
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
              {isSubmitting ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Generating Backlog...</span>
                </div>
              ) : (
                "Generate Agile Backlog"
              )}
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
