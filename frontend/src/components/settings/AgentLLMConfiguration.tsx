import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { FiCpu, FiUser, FiGlobe, FiPlus, FiSave, FiTrash2, FiRefreshCw } from 'react-icons/fi';

interface LLMConfigEntry {
  agentName: string;
  provider: string;
  model: string;
  customModel?: string;
  preset: string;
}

interface AgentLLMConfigurationProps {
  userId: string;
  onSave: (configs: LLMConfigEntry[]) => Promise<void>;
  onRefresh?: () => void;
}

const AGENTS = [
  { key: 'global', name: 'Global Default', description: 'Default configuration for all agents' },
  { key: 'epic_strategist', name: 'Epic Strategist', description: 'Creates high-level epics from product vision' },
  { key: 'feature_decomposer_agent', name: 'Feature Decomposer', description: 'Breaks epics into detailed features' },
  { key: 'user_story_decomposer_agent', name: 'User Story Decomposer', description: 'Creates user stories with acceptance criteria' },
  { key: 'developer_agent', name: 'Developer Agent', description: 'Generates technical tasks with time estimates' },
  { key: 'qa_lead_agent', name: 'QA Lead Agent', description: 'Creates comprehensive test plans and cases' },
];

const PROVIDER_MODELS = {
  openai: [
    'gpt-4o',
    'gpt-4o-mini', 
    'gpt-4-turbo',
    'gpt-4',
    'gpt-3.5-turbo'
  ],
  grok: [
    'grok-beta',
    'grok-4-latest',
    'grok-4'
  ],
  ollama: [
    'llama3.1:8b',
    'llama3.1:70b',
    'qwen2.5:14b-instruct-q4_K_M',
    'qwen2.5:32b',
    'codellama:34b',
    'mistral:7b'
  ]
};

const AgentLLMConfiguration: React.FC<AgentLLMConfigurationProps> = ({
  userId,
  onSave,
  onRefresh
}) => {
  const [configurations, setConfigurations] = useState<LLMConfigEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{success?: boolean, message?: string} | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [useCustomModel, setUseCustomModel] = useState<{[key: string]: boolean}>({});

  useEffect(() => {
    loadConfigurations();
  }, [userId]);

  const loadConfigurations = async () => {
    try {
      setIsLoading(true);
      // Initialize with default global configuration
      const defaultConfigs: LLMConfigEntry[] = AGENTS.map(agent => ({
        agentName: agent.key,
        provider: 'openai',
        model: 'gpt-4o-mini',
        preset: 'balanced'
      }));
      
      setConfigurations(defaultConfigs);
    } catch (error) {
      console.error('Failed to load configurations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfiguration = (agentName: string, updates: Partial<LLMConfigEntry>) => {
    setConfigurations(prev => 
      prev.map(config => 
        config.agentName === agentName 
          ? { ...config, ...updates }
          : config
      )
    );
    setHasChanges(true);
  };

  const toggleCustomModel = (agentName: string) => {
    setUseCustomModel(prev => ({
      ...prev,
      [agentName]: !prev[agentName]
    }));
  };

  const getModelOptions = (provider: string) => {
    return PROVIDER_MODELS[provider as keyof typeof PROVIDER_MODELS] || [];
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setSaveStatus(null);

      await onSave(configurations);
      
      setSaveStatus({ success: true, message: 'LLM configurations saved successfully!' });
      setHasChanges(false);

      setTimeout(() => setSaveStatus(null), 3000);
    } catch (error) {
      setSaveStatus({ 
        success: false, 
        message: `Failed to save configurations: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderAgentConfiguration = (agent: typeof AGENTS[0], config: LLMConfigEntry) => {
    const isCustomModel = useCustomModel[agent.key];
    const modelOptions = getModelOptions(config.provider);

    return (
      <Card key={agent.key} className="border border-primary/30 bg-card/20 backdrop-blur-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FiCpu className="w-5 h-5 text-primary" />
              <div>
                <CardTitle className="text-lg text-foreground">{agent.name}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{agent.description}</p>
              </div>
            </div>
            {agent.key === 'global' && (
              <Badge variant="outline" className="text-primary border-primary">
                Default
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Provider Selection */}
          <div>
            <Label className="text-foreground font-medium mb-2 block">
              LLM Provider
            </Label>
            <Select 
              value={config.provider} 
              onValueChange={(value) => updateConfiguration(agent.key, { 
                provider: value,
                model: getModelOptions(value)[0] || '' // Reset model when provider changes
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">
                  <div className="flex items-center space-x-2">
                    <FiGlobe className="w-4 h-4" />
                    <span>OpenAI (GPT-4, GPT-3.5)</span>
                  </div>
                </SelectItem>
                <SelectItem value="grok">
                  <div className="flex items-center space-x-2">
                    <FiGlobe className="w-4 h-4" />
                    <span>Grok (xAI)</span>
                  </div>
                </SelectItem>
                <SelectItem value="ollama">
                  <div className="flex items-center space-x-2">
                    <FiCpu className="w-4 h-4" />
                    <span>Ollama (Local LLM)</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model Selection with Custom Option */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label className="text-foreground font-medium">
                Model Selection
              </Label>
              <div className="flex items-center space-x-2">
                <Switch
                  id={`custom-${agent.key}`}
                  checked={isCustomModel}
                  onCheckedChange={() => toggleCustomModel(agent.key)}
                />
                <Label htmlFor={`custom-${agent.key}`} className="text-sm text-muted-foreground">
                  Custom Model
                </Label>
              </div>
            </div>

            {isCustomModel ? (
              <div className="space-y-2">
                <Input
                  value={config.customModel || ''}
                  onChange={(e) => updateConfiguration(agent.key, { customModel: e.target.value })}
                  placeholder="Enter custom model name (e.g., gpt-5-mini, claude-3-opus)"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">
                  Enter any model name for future compatibility (gpt-5, claude-3, etc.)
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Select 
                  value={config.model} 
                  onValueChange={(value) => updateConfiguration(agent.key, { model: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelOptions.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Popular models for {config.provider}
                </p>
              </div>
            )}
          </div>

          {/* Preset Selection */}
          <div>
            <Label className="text-foreground font-medium mb-2 block">
              Generation Preset
            </Label>
            <Select 
              value={config.preset} 
              onValueChange={(value) => updateConfiguration(agent.key, { preset: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fast">Fast (Quick responses)</SelectItem>
                <SelectItem value="balanced">Balanced (Good quality/speed)</SelectItem>
                <SelectItem value="high_quality">High Quality (Best output)</SelectItem>
                <SelectItem value="code_focused">Code Focused (Technical tasks)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Configuration Preview */}
          <div className="p-3 rounded-lg border border-primary/20 bg-card/10">
            <div className="text-xs text-muted-foreground space-y-1">
              <div><strong>Provider:</strong> {config.provider}</div>
              <div><strong>Model:</strong> {isCustomModel ? (config.customModel || 'Not specified') : config.model}</div>
              <div><strong>Preset:</strong> {config.preset}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card className="border border-primary/30 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FiCpu className="w-6 h-6 text-primary glow-cyan" />
            <CardTitle className="text-foreground glow-cyan">
              Agent-Specific LLM Configuration
            </CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            {onRefresh && (
              <Button
                onClick={onRefresh}
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                <FiRefreshCw className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Configure different LLM models for each agent. Custom models allow future compatibility with new releases.
        </p>
      </CardHeader>

      <CardContent>
        {/* Save Status */}
        {saveStatus && (
          <Alert className={`mb-6 ${saveStatus.success ? 'border-green-500' : 'border-red-500'}`}>
            <AlertDescription>
              {saveStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Global Configuration */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Global Configuration</h3>
          {renderAgentConfiguration(
            AGENTS[0], 
            configurations.find(c => c.agentName === 'global') || configurations[0]
          )}
        </div>

        {/* Agent-Specific Configurations */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-foreground">Agent-Specific Overrides</h3>
          <p className="text-sm text-muted-foreground -mt-2">
            Leave as default to use global configuration, or customize per agent.
          </p>
          
          <div className="grid gap-6">
            {AGENTS.slice(1).map(agent => {
              const config = configurations.find(c => c.agentName === agent.key) || {
                agentName: agent.key,
                provider: 'openai',
                model: 'gpt-4o-mini',
                preset: 'balanced'
              };
              
              return renderAgentConfiguration(agent, config);
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-4 pt-6 mt-6 border-t border-primary/20">
          <Button 
            onClick={handleSave}
            disabled={!hasChanges || isLoading}
            className="bg-primary hover:bg-primary/80 text-primary-foreground"
          >
            <FiSave className="w-4 h-4 mr-2" />
            {isLoading ? 'Saving...' : 'Save All Configurations'}
          </Button>
          
          <Button 
            onClick={loadConfigurations}
            variant="outline"
            disabled={isLoading}
          >
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Reset to Defaults
          </Button>
        </div>

        {/* Help Text */}
        <div className="mt-6 p-4 rounded-lg border border-blue-500/30 bg-blue-500/10">
          <div className="text-sm text-blue-300 space-y-2">
            <p><strong>🚀 Custom Models:</strong> Enter future model names like "gpt-5", "claude-4", "llama4" for forward compatibility.</p>
            <p><strong>🎯 Agent-Specific:</strong> Each agent can use a different model optimized for its task.</p>
            <p><strong>🔑 API Keys:</strong> Only provider selection affects which API key is used (OpenAI, Grok, or Ollama URL).</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AgentLLMConfiguration;