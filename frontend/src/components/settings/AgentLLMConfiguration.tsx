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
  configuration_mode?: string;  // Added to support database persistence
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
    'gpt-5',
    'gpt-5-mini',
    'gpt-5-nano',
    'gpt-5-chat-latest',
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
    'llama3.3:70b',
    'llama3.3:70b-instruct-q4_K_M',
    'mixtral:8x7b-instruct-v0.1-q2_k',
    'llama3.1:8b',
    'llama3.1:8b-instruct-q4_K_M',
    'llama3.1:70b',
    'qwen2.5:14b-instruct-q4_K_M',
    'qwen2.5:32b',
    'qwen2.5:latest',
    'qwen3:30b',
    'codellama:34b',
    'mistral:7b'
  ]
};

// Model display names for better UX
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  // Ollama models
  'llama3.3:70b': 'Llama 3.3 70B',
  'llama3.3:70b-instruct-q4_K_M': 'Llama 3.3 70B Instruct (Q4)',
  'mixtral:8x7b-instruct-v0.1-q2_k': 'Mixtral 8x7B Instruct (Q2)',
  'llama3.1:8b': 'Llama 3.1 8B',
  'llama3.1:8b-instruct-q4_K_M': 'Llama 3.1 8B Instruct (Q4)',
  'llama3.1:70b': 'Llama 3.1 70B',
  'qwen2.5:14b-instruct-q4_K_M': 'Qwen 2.5 14B Instruct (Q4)',
  'qwen2.5:32b': 'Qwen 2.5 32B',
  'qwen2.5:latest': 'Qwen 2.5 Latest',
  'qwen3:30b': 'Qwen 3 30B',
  'codellama:34b': 'CodeLlama 34B',
  'mistral:7b': 'Mistral 7B',
  // OpenAI models
  'gpt-5': 'GPT-5',
  'gpt-5-mini': 'GPT-5 Mini',
  'gpt-5-nano': 'GPT-5 Nano',
  'gpt-5-chat-latest': 'GPT-5 Chat Latest',
  'gpt-4o': 'GPT-4o',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gpt-4-turbo': 'GPT-4 Turbo',
  'gpt-4': 'GPT-4',
  'gpt-3.5-turbo': 'GPT-3.5 Turbo',
  // Grok models
  'grok-beta': 'Grok Beta',
  'grok-4-latest': 'Grok 4 Latest',
  'grok-4': 'Grok 4'
};

const getModelDisplayName = (model: string): string => {
  return MODEL_DISPLAY_NAMES[model] || model;
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
  const [useAgentSpecific, setUseAgentSpecific] = useState(false);

  // Function to handle configuration mode changes with database persistence
  const handleModeChange = async (newMode: boolean) => {
    console.log('Configuration mode changed:', newMode ? 'agent-specific' : 'global');
    setUseAgentSpecific(newMode);
    
    // Mark as having changes
    setHasChanges(true);
    
    // Save configuration mode immediately
    try {
      setSaveStatus({ message: 'Saving configuration mode...' });
      
      // Prepare configurations with the new mode
      const currentMode = newMode ? 'agent-specific' : 'global';
      
      // Ensure we have at least a global configuration to save the mode
      let configsToSave = configurations.map(config => ({
        ...config,
        configuration_mode: currentMode
      }));
      
      // If no configurations exist, create at least a global one to persist the mode
      if (configsToSave.length === 0) {
        configsToSave = [{
          agentName: 'global',
          provider: 'openai',
          model: 'gpt-5-mini',
          preset: 'high_quality',  // Always use high quality
          configuration_mode: currentMode
        }];
      }
      
      console.log('Saving configuration mode to database:', currentMode);
      console.log('Configurations to save:', configsToSave);
      await onSave(configsToSave);
      
      setSaveStatus({ success: true, message: 'Configuration mode saved successfully!' });
      setTimeout(() => setSaveStatus(null), 3000);
      
      // Refresh configurations to ensure UI stays in sync with backend
      console.log('Refreshing configurations after mode save...');
      await loadConfigurations();
      
    } catch (error: any) {
      console.error('Failed to save configuration mode:', error);
      // Extract error message from response if available
      let errorMessage = 'Failed to save configuration mode';
      if (error?.message) {
        errorMessage = error.message;
      }
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      console.error('Error details:', {
        error,
        message: errorMessage,
        response: error?.response,
        data: error?.response?.data
      });
      
      setSaveStatus({ success: false, message: errorMessage });
      // Revert the UI change on error
      setUseAgentSpecific(!newMode);
    }
  };

  useEffect(() => {
    loadConfigurations();
  }, [userId]);

  const loadConfigurations = async () => {
    try {
      setIsLoading(true);
      
      // Try to load existing configurations from backend
      const response = await fetch(`/api/llm-configurations/${userId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Loaded configurations from backend:', data);
        
        if (data.success) {
          // Always check for configuration mode from the API response
          const databaseMode = data.configuration_mode || 'global';
          const shouldUseAgentSpecific = databaseMode === 'agent-specific';
          
          console.log('Configuration mode from database:', {
            mode: databaseMode,
            shouldUseAgentSpecific
          });
          
          // Set the mode regardless of whether we have configurations
          setUseAgentSpecific(shouldUseAgentSpecific);
          
          if (data.data && data.data.length > 0) {
            // Transform backend format to frontend format - ONLY use saved configurations
            const frontendConfigs: LLMConfigEntry[] = data.data.map((config: any) => ({
              agentName: config.agent_name,  // snake_case -> camelCase
              provider: config.provider,
              model: config.model,
              customModel: undefined, // Backend doesn't return this separately
              preset: config.preset || 'high_quality',  // Always default to high quality
              configuration_mode: config.configuration_mode || data.configuration_mode || 'global'
            }));
            
            console.log('Raw backend response:', data);
            console.log('Transformed frontend configs:', frontendConfigs);
            console.log('Configuration mapping by agent:');
            frontendConfigs.forEach(config => {
              console.log(`  ${config.agentName}: ${config.provider} ${config.model} (${config.preset})`);
            });
            setConfigurations(frontendConfigs);
            return;
          } else {
            // No configurations but we still loaded the mode preference
            console.log('No configurations found, but mode preference loaded:', databaseMode);
            
            // Initialize with default configurations but keep the mode preference
            const defaultConfigs: LLMConfigEntry[] = AGENTS.map(agent => ({
              agentName: agent.key,
              provider: 'openai',
              model: 'gpt-5-mini',
              preset: 'high_quality',  // Always use high quality
              configuration_mode: databaseMode
            }));
            
            setConfigurations(defaultConfigs);
            // Mode has already been set from database, don't override it
            return;
          }
        }
      }
      
      // Fallback: Initialize with default configuration for all agents
      const defaultConfigs: LLMConfigEntry[] = AGENTS.map(agent => ({
        agentName: agent.key,
        provider: 'openai',
        model: 'gpt-5-mini', // Use gpt-5-mini as default instead of gpt-4o-mini
        preset: 'high_quality',  // Always use high quality
        configuration_mode: 'global' // Add default mode
      }));
      
      console.log('Using default configurations:', defaultConfigs);
      setConfigurations(defaultConfigs);
      
      // For default configurations, start in Global mode (no database preference exists yet)
      console.log('Mode for default configs: Global (no database preference exists)');
      setUseAgentSpecific(false);
    } catch (error) {
      console.error('Failed to load configurations:', error);
      // Even if there's an error, provide minimal default configs
      const fallbackConfigs: LLMConfigEntry[] = [{
        agentName: 'global',
        provider: 'openai',
        model: 'gpt-5-mini', // Use gpt-5-mini as default instead of gpt-4o-mini
        preset: 'high_quality'  // Always use high quality
      }];
      setConfigurations(fallbackConfigs);
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

  const applyGlobalToAll = () => {
    const globalConfig = configurations.find(c => c.agentName === 'global');
    if (!globalConfig) return;

    const updatedConfigs = configurations.map(config => 
      config.agentName === 'global' 
        ? config 
        : {
            ...config,
            provider: globalConfig.provider,
            model: globalConfig.model,
            customModel: globalConfig.customModel,
            preset: globalConfig.preset
          }
    );
    
    setConfigurations(updatedConfigs);
    setHasChanges(true);
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

  const renderAgentConfiguration = (agent: typeof AGENTS[0], config: LLMConfigEntry | undefined) => {
    if (!config) {
      return null;
    }
    
    const isCustomModel = useCustomModel[agent.key];
    const modelOptions = getModelOptions(config.provider || 'openai');

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
                    <span>OpenAI</span>
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
                        {getModelDisplayName(model)}
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



          {/* Configuration Preview */}
          <div className="p-3 rounded-lg border border-primary/20 bg-card/10">
            <div className="text-xs text-muted-foreground space-y-1">
              <div><strong>Provider:</strong> {config.provider}</div>
              <div><strong>Model:</strong> {isCustomModel ? (config.customModel || 'Not specified') : config.model}</div>
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
        {/* Loading State */}
        {isLoading && (
          <div className="mb-6 p-4 text-center">
            <p className="text-muted-foreground">Loading LLM configurations...</p>
          </div>
        )}

        {/* Save Status */}
        {saveStatus && (
          <Alert className={`mb-6 ${saveStatus.success ? 'border-green-500' : 'border-red-500'}`}>
            <AlertDescription>
              {saveStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && (
          <>
            {/* Configuration Mode Toggle */}
            <div className="mb-6 p-4 rounded-lg border border-primary/30 bg-card/20">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">Configuration Mode</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Choose how to configure LLM models for your agents
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  <Label htmlFor="agent-specific-toggle" className="text-sm text-foreground">
                    {useAgentSpecific ? 'Agent-Specific' : 'Global'}
                  </Label>
                  <Switch
                    id="agent-specific-toggle"
                    checked={useAgentSpecific}
                    onCheckedChange={handleModeChange}
                  />
                </div>
              </div>
              
              <div className="mt-3 text-xs text-muted-foreground">
                {useAgentSpecific 
                  ? "Configure different models for each agent (Epic Strategist, Feature Decomposer, etc.). You can switch back to Global mode at any time."
                  : "Use one configuration for all agents. Switch to Agent-Specific to customize individual agents."
                }
              </div>
            </div>

            {/* Global Configuration Mode */}
            {!useAgentSpecific && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-foreground mb-4">Global LLM Configuration</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  This configuration will be used by all agents (Epic Strategist, Feature Decomposer, User Story Decomposer, Developer Agent, and QA Lead Agent).
                </p>
                {renderAgentConfiguration(
                  { key: 'global', name: 'Global Configuration', description: 'Used by all agents' }, 
                  configurations.find(c => c.agentName === 'global') || {
                    agentName: 'global',
                    provider: 'openai',
                    model: 'gpt-5-mini', // Use gpt-5-mini as default instead of gpt-4o-mini
                    preset: 'high_quality'  // Always use high quality
                  }
                )}
              </div>
            )}

            {/* Agent-Specific Configuration Mode */}
            {useAgentSpecific && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">Agent-Specific Configurations</h3>
                    <p className="text-sm text-muted-foreground">
                      Configure different models for each agent based on their specific tasks.
                    </p>
                  </div>
                  <Button
                    onClick={applyGlobalToAll}
                    variant="outline"
                    size="sm"
                    className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
                  >
                    <FiRefreshCw className="w-4 h-4 mr-2" />
                    Apply Global to All
                  </Button>
                </div>
                
                <div className="grid gap-6">
                  {AGENTS.filter(agent => agent.key !== 'global').map(agent => {
                    const config = configurations.find(c => c.agentName === agent.key) || {
                      agentName: agent.key,
                      provider: 'openai',
                      model: 'gpt-5-mini', // Use gpt-5-mini as default instead of gpt-4o-mini
                      preset: 'high_quality'  // Always use high quality
                    };
                    
                    return renderAgentConfiguration(agent, config);
                  })}
                </div>
              </div>
            )}

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
            <p><strong>🔄 Global Mode:</strong> One configuration applied to all agents - simple and consistent.</p>
            <p><strong>🎯 Agent-Specific Mode:</strong> Different models per agent - Epic Strategist could use GPT-4, Developer Agent could use CodeLlama, etc.</p>
            <p><strong>🚀 Custom Models:</strong> Enter future model names like "gpt-5", "claude-4", "llama4" for forward compatibility.</p>
            <p><strong>🔑 API Keys:</strong> Provider selection determines which API key is used (OpenAI, Grok, or Ollama URL).</p>
          </div>
        </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default AgentLLMConfiguration;