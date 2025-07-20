import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  FiArrowLeft, 
  FiSave, 
  FiSettings, 
  FiEye, 
  FiEyeOff,
  FiCheckCircle,
  FiAlertCircle,
  FiDatabase,
  FiCpu,
  FiInfo
} from 'react-icons/fi';

interface ConfigData {
  azureDevOpsPat: string;
  azureDevOpsOrg: string;
  azureDevOpsProject: string;
  llmProvider: string;
  areaPath: string;
  openaiApiKey: string;
  grokApiKey: string;
  ollamaModel?: string;
  ollamaUrl?: string;
}

const TronConfigScreen: React.FC = () => {
  const navigate = useNavigate();
  const [config, setConfig] = useState<ConfigData>({
    azureDevOpsPat: '',
    azureDevOpsOrg: '',
    azureDevOpsProject: '',
    llmProvider: 'openai',
    areaPath: '',
    openaiApiKey: '',
    grokApiKey: ''
  });
  
  const [showTokens, setShowTokens] = useState({
    pat: false,
    openai: false,
    grok: false
  });
  
  const [validationStatus, setValidationStatus] = useState<{
    azure: 'idle' | 'validating' | 'success' | 'error';
    ai: 'idle' | 'validating' | 'success' | 'error';
  }>({
    azure: 'idle',
    ai: 'idle'
  });
  
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

  useEffect(() => {
    // Load existing configuration
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  };

  const validateAzureConnection = async () => {
    setValidationStatus(prev => ({ ...prev, azure: 'validating' }));
    
    try {
      const response = await fetch('/api/validate-azure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pat: config.azureDevOpsPat,
          org: config.azureDevOpsOrg,
          project: config.azureDevOpsProject
        })
      });
      
      if (response.ok) {
        setValidationStatus(prev => ({ ...prev, azure: 'success' }));
      } else {
        setValidationStatus(prev => ({ ...prev, azure: 'error' }));
      }
    } catch (error) {
      setValidationStatus(prev => ({ ...prev, azure: 'error' }));
    }
  };

  const validateAIConnection = async () => {
    setValidationStatus(prev => ({ ...prev, ai: 'validating' }));
    
    try {
      const apiKey = config.llmProvider === 'openai' ? config.openaiApiKey : config.grokApiKey;
      const response = await fetch('/api/validate-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: config.llmProvider,
          apiKey: apiKey
        })
      });
      
      if (response.ok) {
        setValidationStatus(prev => ({ ...prev, ai: 'success' }));
      } else {
        setValidationStatus(prev => ({ ...prev, ai: 'error' }));
      }
    } catch (error) {
      setValidationStatus(prev => ({ ...prev, ai: 'error' }));
    }
  };

  const saveConfiguration = async () => {
    setSaveStatus('saving');
    
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus('idle'), 3000);
      } else {
        setSaveStatus('error');
        setTimeout(() => setSaveStatus('idle'), 3000);
      }
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const toggleTokenVisibility = (field: 'pat' | 'openai' | 'grok') => {
    setShowTokens(prev => ({ ...prev, [field]: !prev[field] }));
  };

  return (
    <div className="min-h-screen bg-background tron-grid">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-primary hover:bg-primary/10"
          >
            <FiArrowLeft className="h-4 w-4" />
            RETURN TO MAIN
          </Button>
        </div>

        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <FiSettings className="w-12 h-12 text-primary pulse-glow" />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            SYSTEM <span className="text-primary">CONFIGURATION</span>
          </h1>
          <p className="text-muted-foreground font-mono">
            CONFIGURE ENVIRONMENT VARIABLES AND API CONNECTIONS
          </p>
        </div>

        {/* Configuration Tabs */}
        <div className="max-w-4xl mx-auto">
          <Tabs defaultValue="azure" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 bg-card/50 border border-primary/30">
              <TabsTrigger 
                value="azure" 
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                <FiDatabase className="w-4 h-4 mr-2" />
                AZURE DEVOPS
              </TabsTrigger>
              <TabsTrigger 
                value="ai" 
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                <FiCpu className="w-4 h-4 mr-2" />
                AI PROVIDERS
              </TabsTrigger>
            </TabsList>

            {/* Azure DevOps Configuration */}
            <TabsContent value="azure">
              <Card className="tron-card">
                <CardHeader>
                  <CardTitle className="text-primary flex items-center">
                    <FiDatabase className="w-5 h-5 mr-2" />
                    Azure DevOps Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="azure-org" className="text-foreground">Organization *</Label>
                      <Input
                        id="azure-org"
                        value={config.azureDevOpsOrg}
                        onChange={(e) => setConfig(prev => ({ ...prev, azureDevOpsOrg: e.target.value }))}
                        placeholder="your-organization"
                        className="tron-input"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="azure-project" className="text-foreground">Project *</Label>
                      <Input
                        id="azure-project"
                        value={config.azureDevOpsProject}
                        onChange={(e) => setConfig(prev => ({ ...prev, azureDevOpsProject: e.target.value }))}
                        placeholder="Your Project Name"
                        className="tron-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="azure-pat" className="text-foreground">Personal Access Token *</Label>
                    <div className="relative">
                      <Input
                        id="azure-pat"
                        type={showTokens.pat ? 'text' : 'password'}
                        value={config.azureDevOpsPat}
                        onChange={(e) => setConfig(prev => ({ ...prev, azureDevOpsPat: e.target.value }))}
                        placeholder="Enter your Azure DevOps PAT"
                        className="tron-input pr-12"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 text-primary hover:text-accent"
                        onClick={() => toggleTokenVisibility('pat')}
                      >
                        {showTokens.pat ? <FiEyeOff /> : <FiEye />}
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="area-path" className="text-foreground">Area Path</Label>
                    <Input
                      id="area-path"
                      value={config.areaPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, areaPath: e.target.value }))}
                      placeholder="Project\\Team\\Area"
                      className="tron-input"
                    />
                  </div>

                  <div className="flex gap-4">
                    <Button
                      onClick={validateAzureConnection}
                      disabled={validationStatus.azure === 'validating' || !config.azureDevOpsPat || !config.azureDevOpsOrg}
                      className="tron-button"
                    >
                      {validationStatus.azure === 'validating' ? 'VALIDATING...' : 'VALIDATE CONNECTION'}
                    </Button>
                    
                    {validationStatus.azure === 'success' && (
                      <Alert className="border-green-500/50 bg-green-500/10">
                        <FiCheckCircle className="h-4 w-4 text-green-500" />
                        <AlertDescription className="text-green-400">
                          Azure DevOps connection successful
                        </AlertDescription>
                      </Alert>
                    )}
                    
                    {validationStatus.azure === 'error' && (
                      <Alert className="border-red-500/50 bg-red-500/10">
                        <FiAlertCircle className="h-4 w-4 text-red-500" />
                        <AlertDescription className="text-red-400">
                          Failed to connect to Azure DevOps
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* AI Providers Configuration */}
            <TabsContent value="ai">
              <Card className="tron-card">
                <CardHeader>
                  <CardTitle className="text-primary flex items-center">
                    <FiCpu className="w-5 h-5 mr-2" />
                    AI Provider Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="llm-provider" className="text-foreground">LLM Provider *</Label>
                    <Select
                      value={config.llmProvider}
                      onValueChange={(value) => setConfig(prev => ({ ...prev, llmProvider: value }))}
                    >
                      <SelectTrigger className="tron-input">
                        <SelectValue placeholder="Select AI provider" />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-primary/30">
                        <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                        <SelectItem value="grok">Grok (xAI)</SelectItem>
                        <SelectItem value="ollama">Ollama (Local LLM)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {config.llmProvider === 'openai' && (
                    <div className="space-y-2">
                      <Label htmlFor="openai-key" className="text-foreground">OpenAI API Key *</Label>
                      <div className="relative">
                        <Input
                          id="openai-key"
                          type={showTokens.openai ? 'text' : 'password'}
                          value={config.openaiApiKey}
                          onChange={(e) => setConfig(prev => ({ ...prev, openaiApiKey: e.target.value }))}
                          placeholder="sk-..."
                          className="tron-input pr-12"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 text-primary hover:text-accent"
                          onClick={() => toggleTokenVisibility('openai')}
                        >
                          {showTokens.openai ? <FiEyeOff /> : <FiEye />}
                        </Button>
                      </div>
                    </div>
                  )}

                  {config.llmProvider === 'grok' && (
                    <div className="space-y-2">
                      <Label htmlFor="grok-key" className="text-foreground">Grok API Key *</Label>
                      <div className="relative">
                        <Input
                          id="grok-key"
                          type={showTokens.grok ? 'text' : 'password'}
                          value={config.grokApiKey}
                          onChange={(e) => setConfig(prev => ({ ...prev, grokApiKey: e.target.value }))}
                          placeholder="xai-..."
                          className="tron-input pr-12"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 text-primary hover:text-accent"
                          onClick={() => toggleTokenVisibility('grok')}
                        >
                          {showTokens.grok ? <FiEyeOff /> : <FiEye />}
                        </Button>
                      </div>
                    </div>
                  )}

                  {config.llmProvider === 'ollama' && (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="ollama-model" className="text-foreground">Ollama Model</Label>
                        <Select
                          value={config.ollamaModel || "llama3.1:8b"}
                          onValueChange={(value) => setConfig(prev => ({ ...prev, ollamaModel: value }))}
                        >
                          <SelectTrigger className="tron-input">
                            <SelectValue placeholder="Select Ollama model" />
                          </SelectTrigger>
                          <SelectContent className="bg-card border-primary/30">
                            <SelectItem value="llama3.1:8b">Llama 3.1 8B (Fast)</SelectItem>
                            <SelectItem value="llama3.1:70b">Llama 3.1 70B (High Quality)</SelectItem>
                            <SelectItem value="codellama:34b">CodeLlama 34B (Code Focused)</SelectItem>
                            <SelectItem value="mistral:7b">Mistral 7B (Balanced)</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-sm text-muted-foreground">
                          Select the local model to use for inference
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="ollama-url" className="text-foreground">Ollama Server URL</Label>
                        <Input
                          id="ollama-url"
                          value={config.ollamaUrl || "http://localhost:11434"}
                          onChange={(e) => setConfig(prev => ({ ...prev, ollamaUrl: e.target.value }))}
                          placeholder="http://localhost:11434"
                          className="tron-input"
                        />
                        <p className="text-sm text-muted-foreground">
                          URL where Ollama server is running
                        </p>
                      </div>

                      <Alert className="border-blue-500/50 bg-blue-500/10">
                        <FiInfo className="h-4 w-4 text-blue-500" />
                        <AlertDescription className="text-blue-400">
                          Make sure Ollama is installed and running. No API key required for local inference.
                        </AlertDescription>
                      </Alert>
                    </div>
                  )}

                  <div className="flex gap-4">
                    <Button
                      onClick={validateAIConnection}
                      disabled={validationStatus.ai === 'validating'}
                      className="tron-button"
                    >
                      {validationStatus.ai === 'validating' ? 'VALIDATING...' : 'VALIDATE AI CONNECTION'}
                    </Button>
                    
                    {validationStatus.ai === 'success' && (
                      <Alert className="border-green-500/50 bg-green-500/10">
                        <FiCheckCircle className="h-4 w-4 text-green-500" />
                        <AlertDescription className="text-green-400">
                          AI provider connection successful
                        </AlertDescription>
                      </Alert>
                    )}
                    
                    {validationStatus.ai === 'error' && (
                      <Alert className="border-red-500/50 bg-red-500/10">
                        <FiAlertCircle className="h-4 w-4 text-red-500" />
                        <AlertDescription className="text-red-400">
                          Failed to connect to AI provider
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Save Configuration */}
          <div className="flex justify-center mt-8">
            <Button
              onClick={saveConfiguration}
              disabled={saveStatus === 'saving'}
              className="tron-button px-12 py-4 text-lg"
            >
              <FiSave className="w-5 h-5 mr-2" />
              {saveStatus === 'saving' ? 'SAVING...' : 'SAVE CONFIGURATION'}
            </Button>
          </div>

          {saveStatus === 'success' && (
            <Alert className="border-green-500/50 bg-green-500/10 mt-4">
              <FiCheckCircle className="h-4 w-4 text-green-500" />
              <AlertDescription className="text-green-400">
                Configuration saved successfully
              </AlertDescription>
            </Alert>
          )}

          {saveStatus === 'error' && (
            <Alert className="border-red-500/50 bg-red-500/10 mt-4">
              <FiAlertCircle className="h-4 w-4 text-red-500" />
              <AlertDescription className="text-red-400">
                Failed to save configuration
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
};

export default TronConfigScreen;
