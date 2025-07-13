import React from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { FiCheck, FiAlertTriangle, FiPlay } from 'react-icons/fi';

interface ReviewFormProps {
  onNext?: (data: any) => void;
  onPrevious?: () => void;
  onSubmit?: (data: any) => void;
  initialData?: any;
  isLoading?: boolean;
}

const ReviewForm: React.FC<ReviewFormProps> = ({
  onNext,
  onPrevious,
  onSubmit,
  initialData = {},
  isLoading = false,
}) => {
  // Extract data from initial data - handle nested structure
  const basics = initialData.basics || {};
  const vision = initialData.vision || {};
  const aiConfig = initialData.aiConfig || {};

  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit(initialData);
    } else if (onNext) {
      onNext(initialData);
    }
  };

  const getModelDisplayName = (modelType: string) => {
    switch (modelType) {
      case 'gpt4o': return 'GPT-4o (Recommended)';
      case 'gpt35turbo': return 'GPT-3.5 Turbo (Faster)';
      case 'gpt4': return 'GPT-4 (Legacy)';
      case 'phi3': return 'Phi-3 (Local)';
      default: return modelType || 'Not specified';
    }
  };

  const getCreativityDisplayName = (level: string) => {
    switch (level) {
      case 'conservative': return 'Conservative (Focus on core requirements)';
      case 'balanced': return 'Balanced (Recommended)';
      case 'creative': return 'Creative (Generate more innovative ideas)';
      case 'highly_creative': return 'Highly Creative (Maximum innovation)';
      default: return level || 'Not specified';
    }
  };

  return (
    <div className="bg-card p-6 rounded-lg shadow-md w-full">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-foreground">Review Your Configuration</h2>
          <p className="text-muted-foreground">
            Please review all the information below before proceeding with backlog generation
          </p>
        </div>

        <Alert>
          <FiCheck className="w-4 h-4" />
          <AlertDescription>
            Configuration complete! Your backlog will be generated based on the settings below.
          </AlertDescription>
        </Alert>

        <Accordion type="multiple" className="space-y-2">
          <AccordionItem value="project-basics" className="border rounded-lg">
            <AccordionTrigger className="px-4">
              <div className="flex items-center space-x-2">
                <span className="font-medium">Project Basics</span>
                <Badge variant="default" className="bg-blue-100 text-blue-800">
                  {basics.projectType || 'Not specified'}
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium">Project Name:</span>
                    <p className="text-muted-foreground">{basics.projectName || 'Not specified'}</p>
                  </div>
                  <div>
                    <span className="font-medium">Team Size:</span>
                    <p className="text-muted-foreground">{basics.teamSize || 'Not specified'}</p>
                  </div>
                </div>
                {basics.projectDescription && (
                  <div>
                    <span className="font-medium">Description:</span>
                    <p className="text-muted-foreground mt-1">{basics.projectDescription}</p>
                  </div>
                )}
                {basics.keyRequirements && (
                  <div>
                    <span className="font-medium">Key Requirements:</span>
                    <p className="text-muted-foreground mt-1">{basics.keyRequirements}</p>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="business-vision" className="border rounded-lg">
            <AccordionTrigger className="px-4">
              <div className="flex items-center space-x-2">
                <span className="font-medium">Business Vision & Objectives</span>
                <Badge variant="outline">
                  {vision.businessObjectives?.length || 0} objectives
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-4">
                {vision.businessObjectives && vision.businessObjectives.length > 0 && (
                  <div>
                    <span className="font-medium">Business Objectives:</span>
                    <ul className="mt-2 space-y-1">
                      {vision.businessObjectives.map((objective: string, index: number) => (
                        <li key={index} className="flex items-start space-x-2">
                          <FiCheck className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <span className="text-muted-foreground">{objective}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {vision.successMetrics && vision.successMetrics.length > 0 && (
                  <div>
                    <span className="font-medium">Success Metrics:</span>
                    <ul className="mt-2 space-y-1">
                      {vision.successMetrics.map((metric: string, index: number) => (
                        <li key={index} className="flex items-start space-x-2">
                          <FiCheck className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                          <span className="text-muted-foreground">{metric}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {vision.constraints && (
                  <div>
                    <span className="font-medium">Constraints & Considerations:</span>
                    <p className="text-muted-foreground mt-1">{vision.constraints}</p>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="ai-configuration" className="border rounded-lg">
            <AccordionTrigger className="px-4">
              <div className="flex items-center space-x-2">
                <span className="font-medium">AI Configuration</span>
                <Badge variant="secondary">
                  {getModelDisplayName(aiConfig.modelType).split(' ')[0]}
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium">AI Model:</span>
                    <p className="text-muted-foreground">{getModelDisplayName(aiConfig.modelType)}</p>
                  </div>
                  <div>
                    <span className="font-medium">Creativity Level:</span>
                    <p className="text-muted-foreground">{getCreativityDisplayName(aiConfig.creativityLevel)}</p>
                  </div>
                </div>

                <div>
                  <span className="font-medium">Content Generation Features:</span>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {aiConfig.enableWorkItemLinking && (
                      <div className="flex items-center space-x-2">
                        <FiCheck className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-muted-foreground">Work item linking</span>
                      </div>
                    )}
                    {aiConfig.enhanceRequirements && (
                      <div className="flex items-center space-x-2">
                        <FiCheck className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-muted-foreground">Enhanced requirements</span>
                      </div>
                    )}
                    {aiConfig.generateTestCases && (
                      <div className="flex items-center space-x-2">
                        <FiCheck className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-muted-foreground">Test case generation</span>
                      </div>
                    )}
                    {aiConfig.generateAcceptanceCriteria && (
                      <div className="flex items-center space-x-2">
                        <FiCheck className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-muted-foreground">Acceptance criteria</span>
                      </div>
                    )}
                    {aiConfig.estimateComplexity && (
                      <div className="flex items-center space-x-2">
                        <FiCheck className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-muted-foreground">Complexity estimation</span>
                      </div>
                    )}
                  </div>
                </div>

                {aiConfig.enableAdvancedFeatures && (
                  <div>
                    <span className="font-medium">Advanced Settings:</span>
                    <div className="mt-2 space-y-1">
                      <p className="text-sm text-muted-foreground">
                        Min items: {aiConfig.minBacklogItems || 'Not set'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Max items: {aiConfig.maxBacklogItems || 'Not set'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <Alert variant="destructive">
          <FiAlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <div>
              <strong>Important:</strong> Once you proceed, the AI will begin generating your backlog. 
              This process may take several minutes depending on the complexity of your requirements.
            </div>
          </AlertDescription>
        </Alert>

        <Separator />

        <div className="flex justify-between pt-4">
          {onPrevious && (
            <Button 
              onClick={onPrevious} 
              variant="outline"
              size="lg"
              disabled={isLoading}
            >
              Previous
            </Button>
          )}
          <Button 
            onClick={handleSubmit}
            size="lg"
            disabled={isLoading}
            className="ml-auto min-w-[200px] flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Generating Backlog...</span>
              </>
            ) : (
              <>
                <FiPlay className="w-4 h-4" />
                <span>Generate Backlog</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ReviewForm;
