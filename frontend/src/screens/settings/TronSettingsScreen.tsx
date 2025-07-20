import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { settingsApi, WorkItemLimitsRequest, VisualSettingsRequest } from '../../services/api/settingsApi';
import { userApi, CurrentUser } from '../../services/api/userApi';
import { 
  FiSettings, 
  FiMonitor, 
  FiEye, 
  FiZap,
  FiSave,
  FiRefreshCw,
  FiInfo,
  FiList,
  FiUser,
  FiDatabase,
  FiCpu,
  FiServer
} from 'react-icons/fi';

const TronSettingsScreen: React.FC = () => {
  // Get initial values from localStorage or use defaults
  const getInitialGlowIntensity = () => {
    const saved = localStorage.getItem('tron-glow-intensity');
    return saved ? parseInt(saved) : 70;
  };

  const getInitialWorkItemLimits = () => {
    const saved = localStorage.getItem('work-item-limits');
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      maxEpics: 2,
      maxFeaturesPerEpic: 3,
      maxUserStoriesPerFeature: 5,
      maxTasksPerUserStory: 5,
      maxTestCasesPerUserStory: 5
    };
  };

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [glowIntensity, setGlowIntensity] = useState(getInitialGlowIntensity);
  const [unsavedChanges, setUnsavedChanges] = useState(false);
  
  // Work Item Limits State
  const [workItemLimits, setWorkItemLimits] = useState(getInitialWorkItemLimits);
  const [selectedPreset, setSelectedPreset] = useState('default');
  const [isInitialized, setIsInitialized] = useState(false);
  const [saveAsDefault, setSaveAsDefault] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [sessionId] = useState(`session_${Date.now()}`);
  const [hasCustomSettings, setHasCustomSettings] = useState(false);
  const [useSystemDefaults, setUseSystemDefaults] = useState(false); // Generate unique session ID
  
  // LLM Configuration State
  const [llmConfig, setLlmConfig] = useState({
    provider: 'openai',
    model: 'llama3.1:8b',
    serverUrl: 'http://localhost:11434',
    preset: 'fast'
  });
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // Initialize component
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setIsLoading(true);
        
        // Get current user first
        const userResponse = await userApi.getCurrentUser();
        setCurrentUser(userResponse);
        
        if (!userResponse) {
          throw new Error('Failed to get current user');
        }
        
        // Load settings from backend
        const [workItemLimitsResponse, visualSettingsResponse] = await Promise.all([
          settingsApi.getWorkItemLimits(userResponse.user_id, sessionId),
          settingsApi.getVisualSettings(userResponse.user_id, sessionId)
        ]);
        
        if ((workItemLimitsResponse as any).success && (workItemLimitsResponse as any).data) {
          const data = (workItemLimitsResponse as any).data;
          const limits = data.limits || data; // Handle both new and old format
          
          setWorkItemLimits({
            maxEpics: limits.max_epics || 2,
            maxFeaturesPerEpic: limits.max_features_per_epic || 3,
            maxUserStoriesPerFeature: limits.max_user_stories_per_feature || 5,
            maxTasksPerUserStory: limits.max_tasks_per_user_story || 5,
            maxTestCasesPerUserStory: limits.max_test_cases_per_user_story || 5
          });
          
          // Log if user has custom settings
          if (data.has_custom_settings !== undefined) {
            console.log(`User has custom settings: ${data.has_custom_settings}`);
            setHasCustomSettings(data.has_custom_settings);
            setUseSystemDefaults(!data.has_custom_settings);
          }
        }
        
        if ((visualSettingsResponse as any).success && (visualSettingsResponse as any).data) {
          const data = (visualSettingsResponse as any).data;
          setGlowIntensity(data.glow_intensity || 70);
        }
        
      } catch (error) {
        console.error('Failed to load settings:', error);
        // Fall back to localStorage
        const savedLimits = localStorage.getItem('work-item-limits');
        if (savedLimits) {
          setWorkItemLimits(JSON.parse(savedLimits));
        }
        const savedGlow = localStorage.getItem('tron-glow-intensity');
        if (savedGlow) {
          setGlowIntensity(parseInt(savedGlow));
        }
      } finally {
        setIsLoading(false);
        setIsInitialized(true);
      }
    };
    
    loadSettings();
    loadLlmConfig();
  }, [sessionId]);

  // Apply glow intensity to CSS custom properties
  useEffect(() => {
    const root = document.documentElement;
    const intensity = glowIntensity / 100;
    
    // Update CSS custom properties for glow effects
    root.style.setProperty('--glow-intensity', intensity.toString());
    root.style.setProperty('--glow-cyan-opacity', (0.8 * intensity).toString());
    root.style.setProperty('--glow-strong-opacity', (0.6 * intensity).toString());
    root.style.setProperty('--text-glow-opacity', (0.4 * intensity).toString());
    
    // Only check for unsaved changes after initialization is complete
    if (isInitialized) {
      const savedGlowValue = localStorage.getItem('tron-glow-intensity');
      const savedLimitsValue = localStorage.getItem('work-item-limits');
      
      if (savedGlowValue && savedLimitsValue) {
        const savedLimits = JSON.parse(savedLimitsValue);
        const glowChanged = savedGlowValue !== glowIntensity.toString();
        const limitsChanged = JSON.stringify(savedLimits) !== JSON.stringify(workItemLimits);
        
        setUnsavedChanges(glowChanged || limitsChanged);
      }
    }
  }, [glowIntensity, workItemLimits, isInitialized]);

  const handleSaveSettings = async () => {
    try {
      setIsLoading(true);
      
      if (!currentUser) {
        throw new Error('No current user available');
      }
      
      const scope = saveAsDefault ? 'user_default' : 'session';
      const isUserDefault = saveAsDefault && !useSystemDefaults;
      
      // Save work item limits
      const workItemLimitsRequest: WorkItemLimitsRequest = {
        max_epics: workItemLimits.maxEpics,
        max_features_per_epic: workItemLimits.maxFeaturesPerEpic,
        max_user_stories_per_feature: workItemLimits.maxUserStoriesPerFeature,
        max_tasks_per_user_story: workItemLimits.maxTasksPerUserStory,
        max_test_cases_per_user_story: workItemLimits.maxTestCasesPerUserStory,
        scope,
        session_id: scope === 'session' ? sessionId : undefined,
        is_user_default: isUserDefault
      };
      
      // Save visual settings
      const visualSettingsRequest: VisualSettingsRequest = {
        glow_intensity: glowIntensity,
        scope,
        session_id: scope === 'session' ? sessionId : undefined
      };
      
      // Save both settings
      await Promise.all([
        settingsApi.saveWorkItemLimits(currentUser.user_id, workItemLimitsRequest),
        settingsApi.saveVisualSettings(currentUser.user_id, visualSettingsRequest)
      ]);
      
      // Also save to localStorage as backup
      localStorage.setItem('tron-glow-intensity', glowIntensity.toString());
      localStorage.setItem('work-item-limits', JSON.stringify(workItemLimits));
      
      setUnsavedChanges(false);
      console.log(`Settings saved successfully (${scope})`);
      
    } catch (error) {
      console.error('Failed to save settings:', error);
      // Fall back to localStorage only
      localStorage.setItem('tron-glow-intensity', glowIntensity.toString());
      localStorage.setItem('work-item-limits', JSON.stringify(workItemLimits));
      setUnsavedChanges(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetToDefault = () => {
    setGlowIntensity(70); // Reset to 70% (30% reduction)
    setWorkItemLimits({
      maxEpics: 2,
      maxFeaturesPerEpic: 3,
      maxUserStoriesPerFeature: 5,
      maxTasksPerUserStory: 5,
      maxTestCasesPerUserStory: 5
    });
    setSelectedPreset('default');
  };
  
  const handleSystemDefaultsToggle = async (useDefaults: boolean) => {
    setUseSystemDefaults(useDefaults);
    
    if (useDefaults) {
      // User wants to use system defaults - delete custom settings
      try {
        if (currentUser) {
          // Delete user default settings
          await fetch(`/api/settings/${currentUser.user_id}/work-item-limits?scope=user_default`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
          });
          
          setHasCustomSettings(false);
          console.log('Switched to system defaults');
        }
      } catch (error) {
        console.error('Failed to switch to system defaults:', error);
      }
    } else {
      // User wants to use custom settings - save current values as user defaults
      setHasCustomSettings(true);
      setSaveAsDefault(true); // Automatically enable save as default
    }
  };

  // Load LLM configuration from environment
  const loadLlmConfig = async () => {
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const data = await response.json();
        setLlmConfig({
          provider: data.llmProvider || 'openai',
          model: data.ollamaModel || 'llama3.1:8b',
          serverUrl: data.ollamaUrl || 'http://localhost:11434',
          preset: data.ollamaPreset || 'fast'
        });
      }
    } catch (error) {
      console.error('Failed to load LLM configuration:', error);
    }
  };

  // Save LLM configuration to environment
  const saveLlmConfig = async () => {
    try {
      const configData = {
        llmProvider: llmConfig.provider,
        ...(llmConfig.provider === 'ollama' && {
          ollamaModel: llmConfig.model,
          ollamaUrl: llmConfig.serverUrl,
          ollamaPreset: llmConfig.preset
        })
      };

      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });

      if (response.ok) {
        console.log('LLM configuration saved successfully');
      } else {
        console.error('Failed to save LLM configuration');
      }
    } catch (error) {
      console.error('Failed to save LLM configuration:', error);
    }
  };

  // Load available Ollama models
  const loadAvailableModels = async () => {
    if (llmConfig.provider !== 'ollama') return;
    
    setIsLoadingModels(true);
    try {
      const response = await fetch('/api/ollama/models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
      }
    } catch (error) {
      console.error('Failed to load available models:', error);
    } finally {
      setIsLoadingModels(false);
    }
  };

  // Load models when provider changes to Ollama
  useEffect(() => {
    if (llmConfig.provider === 'ollama') {
      loadAvailableModels();
    }
  }, [llmConfig.provider]);
  
  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    
    const presets = {
      small: {
        maxEpics: 2,
        maxFeaturesPerEpic: 3,
        maxUserStoriesPerFeature: 4,
        maxTasksPerUserStory: 4,
        maxTestCasesPerUserStory: 3
      },
      medium: {
        maxEpics: 3,
        maxFeaturesPerEpic: 4,
        maxUserStoriesPerFeature: 5,
        maxTasksPerUserStory: 5,
        maxTestCasesPerUserStory: 4
      },
      large: {
        maxEpics: 5,
        maxFeaturesPerEpic: 6,
        maxUserStoriesPerFeature: 6,
        maxTasksPerUserStory: 6,
        maxTestCasesPerUserStory: 5
      },
      unlimited: {
        maxEpics: 999,
        maxFeaturesPerEpic: 999,
        maxUserStoriesPerFeature: 999,
        maxTasksPerUserStory: 999,
        maxTestCasesPerUserStory: 999
      }
    };
    
    if (preset !== 'default' && presets[preset as keyof typeof presets]) {
      setWorkItemLimits(presets[preset as keyof typeof presets]);
    }
  };
  
  const calculateMaxItems = () => {
    const { maxEpics, maxFeaturesPerEpic, maxUserStoriesPerFeature, maxTasksPerUserStory, maxTestCasesPerUserStory } = workItemLimits;
    const maxFeatures = maxEpics * maxFeaturesPerEpic;
    const maxUserStories = maxFeatures * maxUserStoriesPerFeature;
    const maxTasks = maxUserStories * maxTasksPerUserStory;
    const maxTestCases = maxUserStories * maxTestCasesPerUserStory;
    
    return { maxFeatures, maxUserStories, maxTasks, maxTestCases };
  };

  const getGlowPreview = () => {
    if (glowIntensity >= 90) return { text: "MAXIMUM", color: "text-red-400", badge: "HIGH" };
    if (glowIntensity >= 70) return { text: "OPTIMAL", color: "text-green-400", badge: "RECOMMENDED" };
    if (glowIntensity >= 50) return { text: "MODERATE", color: "text-yellow-400", badge: "MEDIUM" };
    if (glowIntensity >= 30) return { text: "SUBTLE", color: "text-blue-400", badge: "LOW" };
    return { text: "MINIMAL", color: "text-gray-400", badge: "VERY LOW" };
  };

  const glowPreview = getGlowPreview();

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
                <FiSettings className="w-8 h-8 text-primary glow-cyan" />
                <h1 className="text-4xl font-bold text-foreground tracking-wider glow-cyan">
                  SYSTEM SETTINGS
                </h1>
              </div>
              <p className="text-muted-foreground text-lg">
                Configure visual effects, work item limits, and system preferences
              </p>
            </div>

            {/* Unsaved Changes Alert */}
            {unsavedChanges && (
              <Alert className="tron-card mb-8 border-yellow-500/50 bg-yellow-500/10">
                <FiInfo className="w-4 h-4" />
                <AlertDescription className="text-yellow-300">
                  You have unsaved changes. Click "Save Settings" to apply them permanently.
                </AlertDescription>
              </Alert>
            )}

            {/* Work Item Limits Section */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FiList className="w-6 h-6 text-primary glow-cyan" />
                  <CardTitle className="text-foreground glow-cyan">Work Item Limits</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Preset Selection */}
                <div>
                  <Label className="text-foreground font-medium glow-cyan mb-3 block">
                    Quick Preset
                  </Label>
                  <Select value={selectedPreset} onValueChange={handlePresetChange} disabled={useSystemDefaults}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a preset" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default (2 epics, 3 features/epic, 5 stories/feature)</SelectItem>
                      <SelectItem value="small">Small (96 tasks, 72 test cases)</SelectItem>
                      <SelectItem value="medium">Medium (300 tasks, 240 test cases)</SelectItem>
                      <SelectItem value="large">Large (1,080 tasks, 900 test cases)</SelectItem>
                      <SelectItem value="unlimited">Unlimited (No limits)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* System Defaults Toggle */}
                <div className="flex items-center space-x-3 pt-4 border-t border-primary/20">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="use-system-defaults"
                      checked={useSystemDefaults}
                      onCheckedChange={handleSystemDefaultsToggle}
                      disabled={isLoading}
                    />
                    <Label htmlFor="use-system-defaults" className="text-sm text-foreground">
                      Use System Defaults
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <FiDatabase className="w-3 h-3" />
                    <span>{useSystemDefaults ? 'System Defaults' : 'Custom Settings'}</span>
                  </div>
                </div>
                
                {!useSystemDefaults && (
                  <div className="p-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10">
                    <div className="flex items-center space-x-2 text-yellow-300 text-sm">
                      <FiInfo className="w-4 h-4" />
                      <span>Custom settings will be saved as your personal defaults</span>
                    </div>
                  </div>
                )}

                {/* Custom Limits */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-foreground font-medium glow-cyan mb-2 block">
                      Max Epics
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="50"
                      value={workItemLimits.maxEpics}
                      onChange={(e) => setWorkItemLimits({...workItemLimits, maxEpics: parseInt(e.target.value) || 1})}
                      className="glow-cyan"
                      disabled={useSystemDefaults}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-foreground font-medium glow-cyan mb-2 block">
                      Max Features per Epic
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={workItemLimits.maxFeaturesPerEpic}
                      onChange={(e) => setWorkItemLimits({...workItemLimits, maxFeaturesPerEpic: parseInt(e.target.value) || 1})}
                      className="glow-cyan"
                      disabled={useSystemDefaults}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-foreground font-medium glow-cyan mb-2 block">
                      Max User Stories per Feature
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="15"
                      value={workItemLimits.maxUserStoriesPerFeature}
                      onChange={(e) => setWorkItemLimits({...workItemLimits, maxUserStoriesPerFeature: parseInt(e.target.value) || 1})}
                      className="glow-cyan"
                      disabled={useSystemDefaults}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-foreground font-medium glow-cyan mb-2 block">
                      Max Tasks per User Story
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={workItemLimits.maxTasksPerUserStory}
                      onChange={(e) => setWorkItemLimits({...workItemLimits, maxTasksPerUserStory: parseInt(e.target.value) || 1})}
                      className="glow-cyan"
                      disabled={useSystemDefaults}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-foreground font-medium glow-cyan mb-2 block">
                      Max Test Cases per User Story
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="25"
                      value={workItemLimits.maxTestCasesPerUserStory}
                      onChange={(e) => setWorkItemLimits({...workItemLimits, maxTestCasesPerUserStory: parseInt(e.target.value) || 1})}
                      className="glow-cyan"
                      disabled={useSystemDefaults}
                    />
                  </div>
                </div>

                {/* Max Items Preview */}
                <div className="p-4 rounded-lg border border-primary/30 bg-card/20">
                  <h4 className="text-sm font-medium text-foreground mb-3 glow-cyan">Maximum Items Generated:</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {(() => {
                      const { maxFeatures, maxUserStories, maxTasks, maxTestCases } = calculateMaxItems();
                      return (
                        <>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-primary glow-cyan">{maxFeatures}</div>
                            <div className="text-xs text-muted-foreground">Features</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-accent glow-cyan">{maxUserStories}</div>
                            <div className="text-xs text-muted-foreground">User Stories</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-green-400 glow-cyan">{maxTasks}</div>
                            <div className="text-xs text-muted-foreground">Tasks</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-yellow-400 glow-cyan">{maxTestCases}</div>
                            <div className="text-xs text-muted-foreground">Test Cases</div>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Visual Effects Section */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FiEye className="w-6 h-6 text-primary glow-cyan" />
                  <CardTitle className="text-foreground glow-cyan">Visual Effects</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Glow Intensity Slider */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <FiZap className="w-5 h-5 text-accent glow-cyan" />
                      <label className="text-foreground font-medium glow-cyan">
                        Glow Effect Intensity
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge 
                        variant="outline" 
                        className={`${glowPreview.color} border-current glow-cyan`}
                      >
                        {glowPreview.badge}
                      </Badge>
                      <span className={`font-mono text-sm ${glowPreview.color} glow-cyan`}>
                        {glowIntensity}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {/* Slider */}
                    <div className="relative">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={glowIntensity}
                        onChange={(e) => setGlowIntensity(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider-tron"
                        style={{
                          background: `linear-gradient(to right, 
                            #0ea5e9 0%, 
                            #0ea5e9 ${glowIntensity}%, 
                            #374151 ${glowIntensity}%, 
                            #374151 100%)`
                        }}
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-2">
                        <span>0% (Off)</span>
                        <span>50% (Moderate)</span>
                        <span>100% (Maximum)</span>
                      </div>
                    </div>

                    {/* Live Preview */}
                    <div className="p-4 rounded-lg border border-primary/30 bg-card/20">
                      <h4 className="text-sm font-medium text-foreground mb-3 glow-cyan">Live Preview:</h4>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <FiZap className="w-5 h-5 text-primary glow-cyan" />
                          <span className="text-foreground glow-cyan">Sample Glowing Text</span>
                        </div>
                        <div className="w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent glow-cyan"></div>
                        <div className="flex space-x-2">
                          <div className="w-3 h-3 bg-primary rounded-full glow-cyan"></div>
                          <div className="w-3 h-3 bg-accent rounded-full glow-cyan"></div>
                          <div className="w-3 h-3 bg-green-400 rounded-full glow-cyan"></div>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Status: <span className={`${glowPreview.color} font-mono glow-cyan`}>{glowPreview.text}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* User Information */}
                {currentUser && (
                  <div className="flex items-center space-x-2 pt-4 border-t border-primary/20">
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <FiUser className="w-4 h-4" />
                      <span>Settings for: <strong className="text-foreground">{currentUser.display_name}</strong></span>
                      <span className="text-xs">({currentUser.email})</span>
                    </div>
                  </div>
                )}

                {/* Save as Default Toggle */}
                <div className="flex items-center space-x-3 pt-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="save-as-default"
                      checked={saveAsDefault}
                      onCheckedChange={setSaveAsDefault}
                    />
                    <Label htmlFor="save-as-default" className="text-sm text-foreground">
                      Save as Default for Future Sessions
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <FiUser className="w-3 h-3" />
                    <span>{saveAsDefault ? 'User Default' : 'Session Only'}</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-4 pt-4">
                  <Button 
                    onClick={handleSaveSettings}
                    disabled={!unsavedChanges || isLoading}
                    className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
                  >
                    <FiSave className="w-4 h-4 mr-2" />
                    {isLoading ? 'Saving...' : 'Save Settings'}
                  </Button>
                  
                  <Button 
                    onClick={handleResetToDefault}
                    variant="outline"
                    disabled={isLoading}
                    className="border-accent text-accent hover:bg-accent hover:text-accent-foreground glow-cyan"
                  >
                    <FiRefreshCw className="w-4 h-4 mr-2" />
                    Reset to Default
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* LLM Configuration Section */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 mb-8">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FiCpu className="w-6 h-6 text-primary glow-cyan" />
                  <CardTitle className="text-foreground glow-cyan">LLM Configuration</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* LLM Provider Selection */}
                <div>
                  <Label className="text-foreground font-medium glow-cyan mb-3 block">
                    LLM Provider
                  </Label>
                  <Select 
                    value={llmConfig.provider} 
                    onValueChange={(value) => setLlmConfig(prev => ({ ...prev, provider: value }))}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select LLM provider" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                      <SelectItem value="grok">Grok (xAI)</SelectItem>
                      <SelectItem value="ollama">Ollama (Local LLM)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground mt-2">
                    Choose your preferred language model provider
                  </p>
                </div>

                {/* Ollama-specific Configuration */}
                {llmConfig.provider === 'ollama' && (
                  <div className="space-y-4 p-4 rounded-lg border border-primary/30 bg-card/20">
                    <div className="flex items-center space-x-2 mb-4">
                      <FiServer className="w-4 h-4 text-accent" />
                      <span className="text-sm font-medium text-foreground">Ollama Configuration</span>
                    </div>

                    {/* Model Selection */}
                    <div>
                      <Label className="text-foreground font-medium glow-cyan mb-2 block">
                        Model Selection
                      </Label>
                      <Select 
                        value={llmConfig.model} 
                        onValueChange={(value) => setLlmConfig(prev => ({ ...prev, model: value }))}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select model" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="llama3.1:8b">Llama 3.1 8B (Fast Development)</SelectItem>
                          <SelectItem value="llama3.1:70b">Llama 3.1 70B (High Quality)</SelectItem>
                          <SelectItem value="codellama:34b">CodeLlama 34B (Code Focused)</SelectItem>
                          <SelectItem value="mistral:7b">Mistral 7B (Balanced)</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-sm text-muted-foreground mt-2">
                        Recommended: Start with 8B for development, switch to 70B for production
                      </p>
                    </div>

                    {/* Preset Selection */}
                    <div>
                      <Label className="text-foreground font-medium glow-cyan mb-2 block">
                        Generation Preset
                      </Label>
                      <Select 
                        value={llmConfig.preset} 
                        onValueChange={(value) => setLlmConfig(prev => ({ ...prev, preset: value }))}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select preset" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="fast">Fast (Quick responses)</SelectItem>
                          <SelectItem value="balanced">Balanced (Good quality/speed)</SelectItem>
                          <SelectItem value="high_quality">High Quality (Best output)</SelectItem>
                          <SelectItem value="code_focused">Code Focused (For CodeLlama)</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-sm text-muted-foreground mt-2">
                        Controls generation speed vs quality trade-off
                      </p>
                    </div>

                    {/* Server URL */}
                    <div>
                      <Label className="text-foreground font-medium glow-cyan mb-2 block">
                        Ollama Server URL
                      </Label>
                      <Input
                        value={llmConfig.serverUrl}
                        onChange={(e) => setLlmConfig(prev => ({ ...prev, serverUrl: e.target.value }))}
                        placeholder="http://localhost:11434"
                        className="glow-cyan"
                      />
                      <p className="text-sm text-muted-foreground mt-2">
                        URL where Ollama server is running (default: localhost:11434)
                      </p>
                    </div>

                    {/* Model Status */}
                    <div className="p-3 rounded-lg border border-blue-500/30 bg-blue-500/10">
                      <div className="flex items-center space-x-2 text-blue-300 text-sm">
                        <FiInfo className="w-4 h-4" />
                        <span>
                          {isLoadingModels ? 'Loading models...' : 
                           availableModels.length > 0 ? 
                           `Available models: ${availableModels.join(', ')}` :
                           'No models found. Please install models using: ollama pull llama3.1:8b'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Environment Variable Info */}
                <div className="p-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10">
                  <div className="flex items-center space-x-2 text-yellow-300 text-sm">
                    <FiInfo className="w-4 h-4" />
                    <span>These settings will update your .env file with LLM_PROVIDER and related variables</span>
                  </div>
                </div>

                {/* Save LLM Configuration Button */}
                <div className="flex justify-end pt-4">
                  <Button 
                    onClick={saveLlmConfig}
                    className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
                  >
                    <FiSave className="w-4 h-4 mr-2" />
                    Save LLM Configuration
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Display Settings Section */}
            <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FiMonitor className="w-6 h-6 text-primary glow-cyan" />
                  <CardTitle className="text-foreground glow-cyan">Display Settings</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground glow-cyan">Grid Background</p>
                      <p className="text-sm text-muted-foreground">Toggle the animated grid pattern</p>
                    </div>
                    <div className="w-3 h-3 bg-green-400 rounded-full glow-cyan"></div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground glow-cyan">Matrix Rain Effect</p>
                      <p className="text-sm text-muted-foreground">Animated background particles</p>
                    </div>
                    <div className="w-3 h-3 bg-green-400 rounded-full glow-cyan"></div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground glow-cyan">Scan Line Animation</p>
                      <p className="text-sm text-muted-foreground">Horizontal scanning effect</p>
                    </div>
                    <div className="w-3 h-3 bg-green-400 rounded-full glow-cyan"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TronSettingsScreen;
