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
  parallelProcessing?: {
    enabled: boolean;
    maxWorkers: number | 'unlimited';
  };
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
  const handleModeChange = (newMode: boolean) => {
    console.log('Configuration mode changed:', newMode ? 'agent-specific' : 'global');
    setUseAgentSpecific(newMode);
    
    // Mark as having changes so the mode gets saved with next configuration save
    setHasChanges(true);
    
    // Note: Mode will be persisted to database when configurations are saved
    console.log('Mode change will be persisted to database on next save');
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
        
        if (data.success && data.data && data.data.length > 0) {
          // Transform backend format to frontend format - ONLY use saved configurations
          const frontendConfigs: LLMConfigEntry[] = data.data.map((config: any) => ({
            agentName: config.agent_name,  // snake_case -> camelCase
            provider: config.provider,
            model: config.model,
            customModel: undefined, // Backend doesn't return this separately
            preset: config.preset || 'balanced'
          }));
          
          console.log('Raw backend response:', data);
          console.log('Transformed frontend configs:', frontendConfigs);
          console.log('Configuration mapping by agent:');
          frontendConfigs.forEach(config => {
            console.log(`  ${config.agentName}: ${config.provider} ${config.model} (${config.preset})`);
          });
          setConfigurations(frontendConfigs);
          
          // Configuration mode is now persisted in database and returned by API
          const databaseMode = data.configuration_mode || 'global';
          const shouldUseAgentSpecific = databaseMode === 'agent-specific';
          
          console.log('Mode loaded from database:', {
            databaseMode,
            shouldUseAgentSpecific,
            configCount: frontendConfigs.length,
            note: 'Mode determined by database-persisted user preference'
          });
          
          setUseAgentSpecific(shouldUseAgentSpecific);
          return;
        }
      }
      
      // Fallback: Initialize with default configuration for all agents
      const defaultConfigs: LLMConfigEntry[] = AGENTS.map(agent => ({
        agentName: agent.key,
        provider: 'openai',
        model: 'gpt-5-mini', // Use gpt-5-mini as default instead of gpt-4o-mini
        preset: 'balanced',
        parallelProcessing: {
          enabled: agent.key === 'developer_agent', // Only enable for developer agent by default
          maxWorkers: 2
        }
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
        preset: 'balanced',
        parallelProcessing: {
          enabled: false,
          maxWorkers: 2
        }
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

          {/* Parallel Processing Configuration */}
          <div>
            <Label className="text-foreground font-medium mb-2 block">
              Parallel Processing
            </Label>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Switch
                    id={`parallel-${agent.key}`}
                    checked={config.parallelProcessing?.enabled || false}
                    onCheckedChange={(enabled) => updateConfiguration(agent.key, { 
                      parallelProcessing: {
                        enabled,
                        maxWorkers: enabled ? (config.parallelProcessing?.maxWorkers || 2) : 2
                      }
                    })}
                  />
                  <Label htmlFor={`parallel-${agent.key}`} className="text-sm text-foreground">
                    Enable Parallel Processing
                  </Label>
                </div>
                <Badge 
                  variant={config.parallelProcessing?.enabled ? "default" : "secondary"}
                  className={config.parallelProcessing?.enabled ? "text-green-400 border-green-400" : ""}
                >
                  {config.parallelProcessing?.enabled ? "ON" : "OFF"}
                </Badge>
              </div>
              
              {config.parallelProcessing?.enabled && (
                <div className="space-y-2">
                  <Label className="text-sm text-foreground">
                    Maximum Workers
                  </Label>
                  <div className="flex items-center space-x-2">
                    <Select 
                      value={config.parallelProcessing.maxWorkers === 'unlimited' ? 'unlimited' : config.parallelProcessing.maxWorkers.toString()}
                      onValueChange={(value) => updateConfiguration(agent.key, {
                        parallelProcessing: {
                          enabled: true,
                          maxWorkers: value === 'unlimited' ? 'unlimited' : parseInt(value)
                        }
                      })}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 Worker</SelectItem>
                        <SelectItem value="2">2 Workers</SelectItem>
                        <SelectItem value="3">3 Workers</SelectItem>
                        <SelectItem value="4">4 Workers</SelectItem>
                        <SelectItem value="6">6 Workers</SelectItem>
                        <SelectItem value="8">8 Workers</SelectItem>
                        <SelectItem value="unlimited">Unlimited</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {config.parallelProcessing.maxWorkers === 'unlimited' 
                      ? "No limit on concurrent requests (use with caution - may hit rate limits)"
                      : `Process up to ${config.parallelProcessing.maxWorkers} requests concurrently`
                    }
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="p-3 rounded-lg border border-primary/20 bg-card/10">
            <div className="text-xs text-muted-foreground space-y-1">
              <div><strong>Provider:</strong> {config.provider}</div>
              <div><strong>Model:</strong> {isCustomModel ? (config.customModel || 'Not specified') : config.model}</div>
              <div><strong>Preset:</strong> {config.preset}</div>
              <div><strong>Parallel Processing:</strong> {config.parallelProcessing?.enabled ? `${config.parallelProcessing.maxWorkers} workers` : 'Disabled'}</div>
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
                    preset: 'balanced',
                    parallelProcessing: {
                      enabled: false,
                      maxWorkers: 2
                    }
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
                      preset: 'balanced',
                      parallelProcessing: {
                        enabled: agent.key === 'developer_agent', // Only enable for developer agent by default
                        maxWorkers: 2
                      }
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
            <p><strong>⚡ Parallel Processing:</strong> Enable concurrent request processing for faster generation. Use cautiously to avoid rate limits.</p>
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