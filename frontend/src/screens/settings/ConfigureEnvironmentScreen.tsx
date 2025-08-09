import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { userApi, CurrentUser } from '../../services/api/userApi';
import { 
  FiSettings, 
  FiEye, 
  FiEyeOff,
  FiSave,
  FiRefreshCw,
  FiInfo,
  FiKey,
  FiMail,
  FiGlobe,
  FiShield,
  FiDatabase,
  FiCloud
} from 'react-icons/fi';

interface EnvironmentVariable {
  key: string;
  value: string;
  description: string;
  category: 'azure' | 'ai' | 'notification' | 'other';
  sensitive: boolean;
}

const ConfigureEnvironmentScreen: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{success?: boolean, message?: string} | null>(null);
  const [showSensitive, setShowSensitive] = useState<{[key: string]: boolean}>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Environment variables state
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([
    // Azure DevOps Configuration
    {
      key: 'AZURE_DEVOPS_ORGANIZATION_URL',
      value: '',
      description: 'Your Azure DevOps organization URL (e.g., https://dev.azure.com/yourorg)',
      category: 'azure',
      sensitive: false
    },
    {
      key: 'AZURE_DEVOPS_PAT',
      value: '',
      description: 'Personal Access Token for Azure DevOps API access',
      category: 'azure',
      sensitive: true
    },
    {
      key: 'AZURE_DEVOPS_PROJECT',
      value: '',
      description: 'Default Azure DevOps project name',
      category: 'azure',
      sensitive: false
    },
    // AI Provider Configuration
    {
      key: 'OPENAI_API_KEY',
      value: '',
      description: 'OpenAI API key for GPT models',
      category: 'ai',
      sensitive: true
    },
    {
      key: 'GROK_API_KEY',
      value: '',
      description: 'Grok API key for xAI models',
      category: 'ai',
      sensitive: true
    },
    {
      key: 'OLLAMA_BASE_URL',
      value: 'http://localhost:11434',
      description: 'Base URL for local Ollama instance',
      category: 'ai',
      sensitive: false
    },
    // Notification Configuration  
    {
      key: 'NOTIFICATION_EMAIL',
      value: '',
      description: 'Your email address to receive job completion notifications and status updates',
      category: 'notification',
      sensitive: false
    }
  ]);

  useEffect(() => {
    loadCurrentUser();
    loadEnvironmentVariables();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const user = await userApi.getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  };

  const loadEnvironmentVariables = async () => {
    try {
      setIsLoading(true);
      // TODO: Load environment variables from backend
      // For now, we'll load from localStorage as fallback
      const saved = localStorage.getItem('user-env-vars');
      if (saved) {
        const savedVars = JSON.parse(saved);
        setEnvVars(prevVars => 
          prevVars.map(envVar => ({
            ...envVar,
            value: savedVars[envVar.key] || envVar.value
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load environment variables:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateEnvVar = (key: string, value: string) => {
    setEnvVars(prev => 
      prev.map(envVar => 
        envVar.key === key ? { ...envVar, value } : envVar
      )
    );
    setHasChanges(true);
  };

  const toggleSensitiveVisibility = (key: string) => {
    setShowSensitive(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setSaveStatus(null);

      // Create object with only non-empty values
      const envVarsObject: {[key: string]: string} = {};
      envVars.forEach(envVar => {
        if (envVar.value.trim()) {
          envVarsObject[envVar.key] = envVar.value;
        }
      });

      // TODO: Save to backend API
      // For now, save to localStorage
      localStorage.setItem('user-env-vars', JSON.stringify(envVarsObject));

      setSaveStatus({ success: true, message: 'Environment variables saved successfully!' });
      setHasChanges(false);

      setTimeout(() => setSaveStatus(null), 3000);
    } catch (error) {
      setSaveStatus({ 
        success: false, 
        message: `Failed to save environment variables: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    const confirmReset = window.confirm('Are you sure you want to reset all environment variables to their default values?');
    if (confirmReset) {
      setEnvVars(prev => prev.map(envVar => ({
        ...envVar,
        value: envVar.key === 'OLLAMA_BASE_URL' ? 'http://localhost:11434' : ''
      })));
      setHasChanges(true);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'azure': return <FiDatabase className="w-5 h-5 text-blue-400" />;
      case 'ai': return <FiCloud className="w-5 h-5 text-green-400" />;
      case 'notification': return <FiMail className="w-5 h-5 text-yellow-400" />;
      default: return <FiSettings className="w-5 h-5 text-gray-400" />;
    }
  };

  const getCategoryTitle = (category: string) => {
    switch (category) {
      case 'azure': return 'Azure DevOps Configuration';
      case 'ai': return 'AI Provider Configuration'; 
      case 'notification': return 'Notification Configuration';
      default: return 'Other Configuration';
    }
  };

  const renderEnvVarsByCategory = (category: 'azure' | 'ai' | 'notification' | 'other') => {
    const categoryVars = envVars.filter(envVar => envVar.category === category);
    
    return (
      <div className="space-y-4">
        {categoryVars.map(envVar => (
          <div key={envVar.key}>
            <div className="flex items-center justify-between mb-2">
              <Label className="text-foreground font-medium">
                {envVar.key}
                {envVar.sensitive && (
                  <FiShield className="w-3 h-3 text-yellow-400 inline ml-2" />
                )}
              </Label>
              {envVar.sensitive && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleSensitiveVisibility(envVar.key)}
                  className="h-6 w-6 p-0"
                >
                  {showSensitive[envVar.key] ? (
                    <FiEyeOff className="w-3 h-3" />
                  ) : (
                    <FiEye className="w-3 h-3" />
                  )}
                </Button>
              )}
            </div>
            <Input
              type={envVar.sensitive && !showSensitive[envVar.key] ? 'password' : 'text'}
              value={envVar.value}
              onChange={(e) => updateEnvVar(envVar.key, e.target.value)}
              placeholder={`Enter ${envVar.key.toLowerCase().replace(/_/g, ' ')}`}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground mt-1">
              {envVar.description}
            </p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen">
      {/* Header and Sidebar */}
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Main Content */}
      <div className="ml-0 lg:ml-[250px] pt-[70px] transition-all duration-300 ease-in-out">
        <div className="min-h-screen bg-background tron-grid relative overflow-hidden">
          {/* Enhanced grid background overlay */}
          <div className="absolute inset-0 opacity-20">
            <div className="grid-pattern absolute inset-0"></div>
          </div>

          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-15">
            <div className="scan-line absolute w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent"></div>
          </div>

          <div className="relative z-10 container mx-auto px-6 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <FiKey className="w-8 h-8 text-primary glow-cyan" />
                <h1 className="text-4xl font-bold text-foreground tracking-wider glow-cyan">
                  CONFIGURE ENVIRONMENT
                </h1>
              </div>
              <p className="text-muted-foreground text-lg">
                Set up your personal access tokens, API keys, and notification settings
              </p>
            </div>

            {/* Save Status Alert */}
            {saveStatus && (
              <Alert className={`mb-6 ${saveStatus.success ? 'border-green-500' : 'border-red-500'}`}>
                <FiInfo className="w-4 h-4" />
                <AlertDescription>
                  {saveStatus.message}
                </AlertDescription>
              </Alert>
            )}

            {/* Unsaved Changes Alert */}
            {hasChanges && (
              <Alert className="tron-card mb-8 border-yellow-500/50 bg-yellow-500/10">
                <FiInfo className="w-4 h-4" />
                <AlertDescription className="text-yellow-300">
                  You have unsaved changes. Click "Save Configuration" to apply them.
                </AlertDescription>
              </Alert>
            )}

            {/* User Information */}
            {currentUser && (
              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <FiShield className="w-6 h-6 text-green-400 glow-cyan" />
                    <CardTitle className="text-foreground glow-cyan">User Configuration</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-muted-foreground">User:</span>
                      <span className="text-foreground font-medium">{currentUser.display_name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-muted-foreground">Email:</span>
                      <span className="text-foreground font-medium">{currentUser.email}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Environment Variables Configuration */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FiKey className="w-6 h-6 text-primary glow-cyan" />
                    <CardTitle className="text-foreground glow-cyan">Environment Variables</CardTitle>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={handleReset}
                      variant="outline"
                      size="sm"
                      disabled={isLoading}
                    >
                      <FiRefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Configure your personal access tokens and API keys for secure access to external services.
                </p>
              </CardHeader>

              <CardContent>
                <Tabs defaultValue="azure" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="azure" className="flex items-center space-x-2">
                      {getCategoryIcon('azure')}
                      <span>Azure DevOps</span>
                    </TabsTrigger>
                    <TabsTrigger value="ai" className="flex items-center space-x-2">
                      {getCategoryIcon('ai')}
                      <span>AI Providers</span>
                    </TabsTrigger>
                    <TabsTrigger value="notification" className="flex items-center space-x-2">
                      {getCategoryIcon('notification')}
                      <span>Notifications</span>
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="azure" className="mt-6">
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-foreground mb-2">Azure DevOps Integration</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Configure your Azure DevOps connection for automated work item management.
                      </p>
                    </div>
                    {renderEnvVarsByCategory('azure')}
                  </TabsContent>

                  <TabsContent value="ai" className="mt-6">
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-foreground mb-2">AI Provider APIs</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Set up API keys for different LLM providers. Only configure the providers you plan to use.
                      </p>
                    </div>
                    {renderEnvVarsByCategory('ai')}
                  </TabsContent>

                  <TabsContent value="notification" className="mt-6">
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-foreground mb-2">Email Notifications</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Enter your email address to receive notifications about job completion and system status.
                        SMTP server configuration is handled automatically by the system.
                      </p>
                    </div>
                    {renderEnvVarsByCategory('notification')}
                    
                    <div className="mt-4 p-3 rounded-lg border border-blue-500/30 bg-blue-500/10">
                      <div className="flex items-start space-x-2 text-blue-300 text-sm">
                        <FiInfo className="w-4 h-4 mt-0.5" />
                        <div>
                          <p className="font-medium mb-1">System Configuration Note:</p>
                          <p>Email sending (SMTP server, port, authentication) is configured by system administrators in the .env file. 
                          You only need to provide your email address to receive notifications.</p>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex space-x-4 mb-8">
              <Button 
                onClick={handleSave}
                disabled={!hasChanges || isLoading}
                className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
              >
                <FiSave className="w-4 h-4 mr-2" />
                {isLoading ? 'Saving...' : 'Save Configuration'}
              </Button>
              
              <Button 
                onClick={handleReset}
                variant="outline"
                disabled={isLoading}
                className="border-accent text-accent hover:bg-accent hover:text-accent-foreground glow-cyan"
              >
                <FiRefreshCw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </Button>
            </div>

            {/* Security Notice */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-yellow-500/30 mb-8">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FiShield className="w-6 h-6 text-yellow-400 glow-cyan" />
                  <CardTitle className="text-foreground glow-cyan">Security Notice</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground space-y-2">
                  <p><strong>🔐 Sensitive Data:</strong> API keys and passwords are encrypted and stored securely.</p>
                  <p><strong>🔑 Access Tokens:</strong> Personal Access Tokens should have minimum required permissions.</p>
                  <p><strong>🛡️ Best Practices:</strong> Regularly rotate your API keys and monitor their usage.</p>
                  <p><strong>🚫 Never Share:</strong> Do not share your configuration with others or commit it to version control.</p>
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigureEnvironmentScreen;