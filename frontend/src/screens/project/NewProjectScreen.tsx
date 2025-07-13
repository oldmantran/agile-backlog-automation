import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Badge } from '../../components/ui/badge';
import { Separator } from '../../components/ui/separator';
import { Progress } from '../../components/ui/progress';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Checkbox } from '../../components/ui/checkbox';
import { 
  FiPlus, 
  FiArrowLeft, 
  FiCheckCircle, 
  FiSettings,
  FiUsers,
  FiTarget,
  FiCode,
  FiDatabase,
  FiCloud,
  FiGitBranch,
  FiFolder,
  FiArrowRight
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface ProjectConfig {
  name: string;
  description: string;
  organization: string;
  teamProject: string;
  areaPath: string;
  iterationPath: string;
  projectType: string;
  features: string[];
  agents: string[];
}

const steps = [
  { title: 'Project Details', description: 'Basic project information' },
  { title: 'Azure DevOps', description: 'Configure ADO integration' },
  { title: 'Features & Agents', description: 'Select automation features' },
  { title: 'Confirmation', description: 'Review and create project' },
];

const NewProjectScreen: React.FC = () => {
  const navigate = useNavigate();
  // TODO: Add proper toast notification
  // const toast = useToast();
  const [activeStep, setActiveStep] = useState(0);

  const [isCreating, setIsCreating] = useState(false);
  const [config, setConfig] = useState<ProjectConfig>({
    name: '',
    description: '',
    organization: '',
    teamProject: '',
    areaPath: '',
    iterationPath: '',
    projectType: 'agile',
    features: ['backlog_enhancement', 'quality_checks'],
    agents: ['epic_strategist', 'user_story_decomposer'],
  });
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');

  const projectTypes = [
    { value: 'agile', label: 'Agile Development', description: 'Standard agile project with sprints and user stories' },
    { value: 'scrum', label: 'Scrum Framework', description: 'Scrum-based project with defined roles and ceremonies' },
    { value: 'kanban', label: 'Kanban Board', description: 'Continuous flow project with WIP limits' },
    { value: 'hybrid', label: 'Hybrid Approach', description: 'Custom mix of agile methodologies' },
  ];

  const availableFeatures = [
    { value: 'backlog_enhancement', label: 'Backlog Enhancement', description: 'Automated backlog item improvement' },
    { value: 'quality_checks', label: 'Quality Assurance', description: 'Automated quality checks and validation' },
    { value: 'test_automation', label: 'Test Case Generation', description: 'AI-powered test case creation' },
    { value: 'story_estimation', label: 'Story Point Estimation', description: 'Automated story point estimation' },
    { value: 'dependency_analysis', label: 'Dependency Analysis', description: 'Automatic dependency detection' },
    { value: 'sprint_planning', label: 'Sprint Planning', description: 'AI-assisted sprint planning' },
  ];

  const availableAgents = [
    { value: 'epic_strategist', label: 'Epic Strategist', description: 'Breaks down large initiatives', icon: FiTarget },
    { value: 'user_story_decomposer', label: 'User Story Decomposer', description: 'Creates detailed user stories', icon: FiUsers },
    { value: 'qa_lead_agent', label: 'QA Lead Agent', description: 'Quality assurance and testing', icon: FiCheckCircle },
    { value: 'developer_agent', label: 'Developer Agent', description: 'Technical task management', icon: FiCode },
    { value: 'feature_decomposer', label: 'Feature Decomposer', description: 'Feature breakdown and planning', icon: FiFolder },
  ];

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
    }
  };

  const handlePrevious = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };

  const handleCreateProject = async () => {
    setIsCreating(true);
    setProgress(0);
    setCurrentOperation('Initializing project creation...');

    try {
      await simulateProjectCreation();
      // TODO: Add proper toast notification
      console.log(`Project Created Successfully: ${config.name} has been set up with all selected features`);
      navigate('/dashboard');
    } catch (error) {
      // TODO: Add proper toast notification
      console.error('Project Creation Failed: An error occurred while creating the project', error);
    } finally {
      setIsCreating(false);
    }
  };

  const simulateProjectCreation = async () => {
    const operations = [
      { text: 'Validating Azure DevOps connection...', duration: 1000 },
      { text: 'Creating project structure...', duration: 1500 },
      { text: 'Setting up area paths and iterations...', duration: 1200 },
      { text: 'Configuring AI agents...', duration: 1800 },
      { text: 'Initializing backlog automation features...', duration: 1500 },
      { text: 'Setting up quality checks...', duration: 1000 },
      { text: 'Creating initial project dashboard...', duration: 800 },
      { text: 'Project setup completed successfully', duration: 500 },
    ];

    for (let i = 0; i < operations.length; i++) {
      setCurrentOperation(operations[i].text);
      setProgress((i + 1) / operations.length * 100);
      await new Promise(resolve => setTimeout(resolve, operations[i].duration));
    }
  };

  const isStepValid = () => {
    switch (activeStep) {
      case 0:
        return config.name.trim() && config.description.trim();
      case 1:
        return config.organization.trim() && config.teamProject.trim();
      case 2:
        return config.features.length > 0 && config.agents.length > 0;
      default:
        return true;
    }
  };

  return (
    <div className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="flex items-center"
          >
            <FiArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-primary mb-2 flex items-center">
            <FiPlus className="mr-3 h-6 w-6" />
            Create New Project
          </h1>
          <p className="text-muted-foreground">
            Set up a new agile project with AI-powered automation
          </p>
        </div>

        {/* Progress Stepper */}
        <Card>
          <CardContent className="pt-6">
            {/* Custom Stepper Implementation */}
            <div className="flex items-center justify-between mb-8">
              {steps.map((step, index) => (
                <div key={index} className="flex items-center">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                    index < activeStep 
                      ? 'bg-primary text-primary-foreground' 
                      : index === activeStep 
                        ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2' 
                        : 'bg-muted text-muted-foreground'
                  }`}>
                    {index < activeStep ? (
                      <FiCheckCircle className="h-4 w-4" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-px ml-4 ${
                      index < activeStep ? 'bg-primary' : 'bg-muted'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            
            {/* Step Content */}
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-lg font-medium">{steps[activeStep].title}</h3>
                <p className="text-sm text-muted-foreground">{steps[activeStep].description}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Step Content */}
        <Card className="min-h-[400px]">
          <CardContent className="pt-6">
            {activeStep === 0 && (
              <div className="space-y-6">
                <h2 className="text-lg font-medium">Project Details</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="project-name">Project Name *</Label>
                    <Input
                      id="project-name"
                      placeholder="e.g., Customer Portal Enhancement"
                      value={config.name}
                      onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="project-type">Project Type *</Label>
                    <Select
                      value={config.projectType}
                      onValueChange={(value) => setConfig(prev => ({ ...prev, projectType: value }))}
                    >
                      <SelectTrigger id="project-type">
                        <SelectValue placeholder="Select project type" />
                      </SelectTrigger>
                      <SelectContent>
                        {projectTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="project-description">Project Description *</Label>
                  <Textarea
                    id="project-description"
                    placeholder="Describe the goals and scope of your project..."
                    value={config.description}
                    onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                  />
                </div>

                {config.projectType && (
                  <Alert className="rounded-md">
                    <AlertDescription>
                      <div>
                        <h4 className="font-medium mb-1">
                          {projectTypes.find(t => t.value === config.projectType)?.label}
                        </h4>
                        <p className="text-sm">
                          {projectTypes.find(t => t.value === config.projectType)?.description}
                        </p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {activeStep === 1 && (
              <div className="space-y-6">
                <h2 className="text-lg font-medium">Azure DevOps Configuration</h2>
                <Alert variant="destructive" className="rounded-md">
                  <AlertDescription>
                    <div>
                      <h4 className="font-medium mb-1">Azure DevOps Integration</h4>
                      <p className="text-sm">
                        Ensure you have proper permissions to create work items in the target project.
                      </p>
                    </div>
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="organization">Organization *</Label>
                    <Input
                      id="organization"
                      placeholder="e.g., mycompany"
                      value={config.organization}
                      onChange={(e) => setConfig(prev => ({ ...prev, organization: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="team-project">Team Project *</Label>
                    <Input
                      id="team-project"
                      placeholder="e.g., MyTeamProject"
                      value={config.teamProject}
                      onChange={(e) => setConfig(prev => ({ ...prev, teamProject: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="area-path">Area Path</Label>
                    <Input
                      id="area-path"
                      placeholder="e.g., MyTeamProject\\MyFeature"
                      value={config.areaPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, areaPath: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="iteration-path">Iteration Path</Label>
                    <Input
                      id="iteration-path"
                      placeholder="e.g., MyTeamProject\\Sprint 1"
                      value={config.iterationPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, iterationPath: e.target.value }))}
                    />
                  </div>
                </div>
              </div>
            )}

            {activeStep === 2 && (
              <div className="space-y-6">
                <h2 className="text-lg font-medium">Features & AI Agents</h2>
                
                <div>
                  <h3 className="font-medium mb-3">Select Automation Features:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {availableFeatures.map((feature) => (
                      <div key={feature.value} className="flex items-start space-x-2">
                        <Checkbox
                          id={`feature-${feature.value}`}
                          checked={config.features.includes(feature.value)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setConfig(prev => ({ ...prev, features: [...prev.features, feature.value] }));
                            } else {
                              setConfig(prev => ({ ...prev, features: prev.features.filter(f => f !== feature.value) }));
                            }
                          }}
                        />
                        <div className="space-y-0.5">
                          <Label htmlFor={`feature-${feature.value}`} className="font-medium">
                            {feature.label}
                          </Label>
                          <p className="text-sm text-muted-foreground">{feature.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="font-medium mb-3">Select AI Agents:</h3>
                  <div className="space-y-3">
                    {availableAgents.map((agent) => (
                      <div key={agent.value} className="flex items-start space-x-2">
                        <Checkbox
                          id={`agent-${agent.value}`}
                          checked={config.agents.includes(agent.value)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setConfig(prev => ({ ...prev, agents: [...prev.agents, agent.value] }));
                            } else {
                              setConfig(prev => ({ ...prev, agents: prev.agents.filter(a => a !== agent.value) }));
                            }
                          }}
                        />
                        <div className="flex items-start space-x-2">
                          <agent.icon className="h-5 w-5 text-primary mt-0.5" />
                          <div className="space-y-0.5">
                            <Label htmlFor={`agent-${agent.value}`} className="font-medium">
                              {agent.label}
                            </Label>
                            <p className="text-sm text-muted-foreground">{agent.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeStep === 3 && (
              <div className="space-y-6">
                <h2 className="text-lg font-medium">Review & Create Project</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="border">
                    <CardHeader>
                      <CardTitle className="text-base">Project Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Name:</span>
                          <span className="text-sm">{config.name}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Type:</span>
                          <Badge>{projectTypes.find(t => t.value === config.projectType)?.label}</Badge>
                        </div>
                        <div>
                          <span className="text-sm font-medium mb-1 block">Description:</span>
                          <p className="text-sm text-muted-foreground">{config.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border">
                    <CardHeader>
                      <CardTitle className="text-base">Azure DevOps</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Organization:</span>
                          <span className="text-sm">{config.organization}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Project:</span>
                          <span className="text-sm">{config.teamProject}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Area Path:</span>
                          <span className="text-sm">{config.areaPath || 'Root'}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border">
                    <CardHeader>
                      <CardTitle className="text-base">Selected Features</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {config.features.map((featureValue) => {
                          const feature = availableFeatures.find(f => f.value === featureValue);
                          return (
                            <div key={featureValue} className="flex items-center space-x-2">
                              <FiCheckCircle className="h-3 w-3 text-green-500" />
                              <span className="text-sm">{feature?.label}</span>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border">
                    <CardHeader>
                      <CardTitle className="text-base">AI Agents</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {config.agents.map((agentValue) => {
                          const agent = availableAgents.find(a => a.value === agentValue);
                          return (
                            <div key={agentValue} className="flex items-center space-x-2">
                              {agent?.icon && <agent.icon className="h-3 w-3 text-primary" />}
                              <span className="text-sm">{agent?.label}</span>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {isCreating && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-6">
                      <div className="space-y-4">
                        <h4 className="font-bold text-blue-700">Creating Project...</h4>
                        <Progress value={progress} className="h-3" />
                        <p className="text-sm text-blue-600">{currentOperation}</p>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            onClick={handlePrevious}
            disabled={activeStep === 0 || isCreating}
            variant="outline"
          >
            Previous
          </Button>

          <div className="flex items-center space-x-4">
            {activeStep < steps.length - 1 ? (
              <Button
                onClick={handleNext}
                disabled={!isStepValid() || isCreating}
                className="flex items-center"
              >
                Next
                <FiArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleCreateProject}
                disabled={!isStepValid() || isCreating}
                size="lg"
                className="flex items-center"
              >
                {isCreating ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-2"></div>
                    Creating Project...
                  </>
                ) : (
                  <>
                    <FiPlus className="mr-2 h-4 w-4" />
                    Create Project
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewProjectScreen;
