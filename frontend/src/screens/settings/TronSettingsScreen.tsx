import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { 
  FiSettings, 
  FiMonitor, 
  FiEye, 
  FiZap,
  FiSave,
  FiRefreshCw,
  FiInfo
} from 'react-icons/fi';

const TronSettingsScreen: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [glowIntensity, setGlowIntensity] = useState(70); // Default to 70% (30% reduction from 100%)
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Load saved settings on component mount
  useEffect(() => {
    const savedGlowIntensity = localStorage.getItem('tron-glow-intensity');
    if (savedGlowIntensity) {
      setGlowIntensity(parseInt(savedGlowIntensity));
    }
  }, []);

  // Apply glow intensity to CSS custom properties
  useEffect(() => {
    const root = document.documentElement;
    const intensity = glowIntensity / 100;
    
    // Update CSS custom properties for glow effects
    root.style.setProperty('--glow-intensity', intensity.toString());
    root.style.setProperty('--glow-cyan-opacity', (0.8 * intensity).toString());
    root.style.setProperty('--glow-strong-opacity', (0.6 * intensity).toString());
    root.style.setProperty('--text-glow-opacity', (0.4 * intensity).toString());
    
    // Mark as having unsaved changes if different from saved value
    const savedValue = localStorage.getItem('tron-glow-intensity');
    setUnsavedChanges(savedValue !== glowIntensity.toString());
  }, [glowIntensity]);

  const handleSaveSettings = () => {
    localStorage.setItem('tron-glow-intensity', glowIntensity.toString());
    setUnsavedChanges(false);
  };

  const handleResetToDefault = () => {
    setGlowIntensity(70); // Reset to 70% (30% reduction)
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
                Configure visual effects and system preferences
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

                {/* Action Buttons */}
                <div className="flex space-x-4 pt-4 border-t border-primary/20">
                  <Button 
                    onClick={handleSaveSettings}
                    disabled={!unsavedChanges}
                    className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
                  >
                    <FiSave className="w-4 h-4 mr-2" />
                    Save Settings
                  </Button>
                  
                  <Button 
                    onClick={handleResetToDefault}
                    variant="outline"
                    className="border-accent text-accent hover:bg-accent hover:text-accent-foreground glow-cyan"
                  >
                    <FiRefreshCw className="w-4 h-4 mr-2" />
                    Reset to Default
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
