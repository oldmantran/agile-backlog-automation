import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { Textarea } from '../components/ui/textarea';
import { 
  FiArrowLeft, 
  FiRefreshCw, 
  FiSettings,
  FiCheckCircle,
  FiLoader,
  FiPlay,
  FiPause,
  FiActivity
} from 'react-icons/fi';

interface SweeperConfig {
  targetArea: string;
  iterationPath: string;
  includeAcceptanceCriteria: boolean;
  includeTaskDecomposition: boolean;
  includeQualityCheck: boolean;
  enhanceRequirements: boolean;
  maxItemsPerRun: number;
}

interface SweeperStatus {
  isRunning: boolean;
  progress: number;
  currentItem: string;
  processedItems: number;
  totalItems: number;
  errors: string[];
  completedActions: string[];
}

const TronBacklogSweeperScreen: React.FC = () => {
  const navigate = useNavigate();
  const [config, setConfig] = useState<SweeperConfig>({
    targetArea: '',
    iterationPath: '',
    includeAcceptanceCriteria: true,
    includeTaskDecomposition: true,
    includeQualityCheck: true,
    enhanceRequirements: true,
    maxItemsPerRun: 50
  });
  
  const [status, setStatus] = useState<SweeperStatus>({
    isRunning: false,
    progress: 0,
    currentItem: '',
    processedItems: 0,
    totalItems: 0,
    errors: [],
    completedActions: []
  });
  
  const [logs, setLogs] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      const response = await fetch('/api/sweeper/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(prev => ({ ...prev, ...data }));
      }
    } catch (error) {
      console.error('Failed to load sweeper configuration:', error);
    }
  };

  const saveConfiguration = async () => {
    try {
      const response = await fetch('/api/sweeper/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuration saved successfully' });
      } else {
        setMessage({ type: 'error', text: 'Failed to save configuration' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error saving configuration' });
    }
  };

  const startSweeper = async () => {
    setStatus(prev => ({ ...prev, isRunning: true, progress: 0, errors: [], completedActions: [] }));
    setLogs([]);
    setMessage(null);
    
    try {
      const response = await fetch('/api/sweeper/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        // Start polling for status updates
        pollSweeperStatus();
      } else {
        setMessage({ type: 'error', text: 'Failed to start backlog sweeper' });
        setStatus(prev => ({ ...prev, isRunning: false }));
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error starting backlog sweeper' });
      setStatus(prev => ({ ...prev, isRunning: false }));
    }
  };

  const stopSweeper = async () => {
    try {
      const response = await fetch('/api/sweeper/stop', { method: 'POST' });
      if (response.ok) {
        setStatus(prev => ({ ...prev, isRunning: false }));
        setMessage({ type: 'info', text: 'Backlog sweeper stopped' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error stopping sweeper' });
    }
  };

  const pollSweeperStatus = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/sweeper/status');
        if (response.ok) {
          const statusData = await response.json();
          setStatus(statusData);
          
          // Add new logs if any
          if (statusData.logs && statusData.logs.length > logs.length) {
            setLogs(statusData.logs);
          }
          
          // Stop polling if sweeper is complete
          if (!statusData.isRunning) {
            clearInterval(interval);
            if (statusData.errors.length === 0) {
              setMessage({ type: 'success', text: `Backlog sweeper completed successfully. Processed ${statusData.processedItems} items.` });
            } else {
              setMessage({ type: 'error', text: `Backlog sweeper completed with ${statusData.errors.length} errors.` });
            }
          }
        }
      } catch (error) {
        clearInterval(interval);
        setMessage({ type: 'error', text: 'Lost connection to sweeper process' });
        setStatus(prev => ({ ...prev, isRunning: false }));
      }
    }, 2000);
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
            <FiRefreshCw className={`w-12 h-12 text-accent pulse-glow ${status.isRunning ? 'animate-spin' : ''}`} />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            BACKLOG <span className="text-accent">SWEEPER</span>
          </h1>
          <p className="text-muted-foreground font-mono">
            AI-POWERED BACKLOG VALIDATION AND ENHANCEMENT
          </p>
        </div>

        <div className="max-w-6xl mx-auto space-y-6">
          {/* Configuration */}
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary flex items-center">
                <FiSettings className="w-5 h-5 mr-2" />
                Sweeper Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="target-area" className="text-foreground">Target Area Path</Label>
                  <Input
                    id="target-area"
                    value={config.targetArea}
                    onChange={(e) => setConfig(prev => ({ ...prev, targetArea: e.target.value }))}
                    placeholder="Project\\Team\\Area"
                    className="tron-input"
                    disabled={status.isRunning}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="iteration-path" className="text-foreground">Iteration Path (Optional)</Label>
                  <Input
                    id="iteration-path"
                    value={config.iterationPath}
                    onChange={(e) => setConfig(prev => ({ ...prev, iterationPath: e.target.value }))}
                    placeholder="Sprint\\Current"
                    className="tron-input"
                    disabled={status.isRunning}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-foreground">Enhancement Options</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={config.includeAcceptanceCriteria}
                      onCheckedChange={(checked) => 
                        setConfig(prev => ({ ...prev, includeAcceptanceCriteria: !!checked }))
                      }
                      disabled={status.isRunning}
                    />
                    <Label className="text-foreground">Include Acceptance Criteria Enhancement</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={config.includeTaskDecomposition}
                      onCheckedChange={(checked) => 
                        setConfig(prev => ({ ...prev, includeTaskDecomposition: !!checked }))
                      }
                      disabled={status.isRunning}
                    />
                    <Label className="text-foreground">Include Task Decomposition</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={config.includeQualityCheck}
                      onCheckedChange={(checked) => 
                        setConfig(prev => ({ ...prev, includeQualityCheck: !!checked }))
                      }
                      disabled={status.isRunning}
                    />
                    <Label className="text-foreground">Include Quality Validation</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={config.enhanceRequirements}
                      onCheckedChange={(checked) => 
                        setConfig(prev => ({ ...prev, enhanceRequirements: !!checked }))
                      }
                      disabled={status.isRunning}
                    />
                    <Label className="text-foreground">Enhance Requirements</Label>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-items" className="text-foreground">Maximum Items Per Run</Label>
                <Input
                  id="max-items"
                  type="number"
                  min="1"
                  max="200"
                  value={config.maxItemsPerRun}
                  onChange={(e) => setConfig(prev => ({ ...prev, maxItemsPerRun: parseInt(e.target.value) || 50 }))}
                  className="tron-input w-32"
                  disabled={status.isRunning}
                />
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={saveConfiguration}
                  disabled={status.isRunning}
                  variant="outline"
                  className="border-primary/50 text-primary hover:bg-primary/10"
                >
                  <FiSettings className="w-4 h-4 mr-2" />
                  SAVE CONFIG
                </Button>
                
                {!status.isRunning ? (
                  <Button
                    onClick={startSweeper}
                    disabled={!config.targetArea}
                    className="tron-button"
                  >
                    <FiPlay className="w-4 h-4 mr-2" />
                    START SWEEPER
                  </Button>
                ) : (
                  <Button
                    onClick={stopSweeper}
                    variant="destructive"
                    className="bg-destructive hover:bg-destructive/90"
                  >
                    <FiPause className="w-4 h-4 mr-2" />
                    STOP SWEEPER
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Status Display */}
          {status.isRunning && (
            <Card className="tron-card">
              <CardHeader>
                <CardTitle className="text-accent flex items-center">
                  <FiActivity className="w-5 h-5 mr-2 animate-pulse" />
                  Sweeper Status - ACTIVE
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-foreground">Progress</span>
                    <span className="text-primary">{status.progress}%</span>
                  </div>
                  <Progress value={status.progress} className="h-3" />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Current Item:</span>
                    <p className="text-foreground font-mono">{status.currentItem || 'Initializing...'}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Processed:</span>
                    <p className="text-foreground font-mono">{status.processedItems} / {status.totalItems}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Errors:</span>
                    <p className="text-foreground font-mono">{status.errors.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Messages */}
          {message && (
            <Alert className={`border-2 ${
              message.type === 'success' ? 'border-green-500/50 bg-green-500/10' :
              message.type === 'error' ? 'border-red-500/50 bg-red-500/10' :
              'border-blue-500/50 bg-blue-500/10'
            }`}>
              {message.type === 'success' ? <FiCheckCircle className="h-4 w-4 text-green-500" /> :
               message.type === 'error' ? <FiActivity className="h-4 w-4 text-red-500" /> :
               <FiLoader className="h-4 w-4 text-blue-500" />}
              <AlertDescription className={
                message.type === 'success' ? 'text-green-400' :
                message.type === 'error' ? 'text-red-400' :
                'text-blue-400'
              }>
                {message.text}
              </AlertDescription>
            </Alert>
          )}

          {/* Logs */}
          {logs.length > 0 && (
            <Card className="tron-card">
              <CardHeader>
                <CardTitle className="text-primary">Process Logs</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={logs.join('\n')}
                  readOnly
                  className="tron-input h-64 font-mono text-sm"
                  placeholder="Process logs will appear here..."
                />
              </CardContent>
            </Card>
          )}

          {/* Completed Actions */}
          {status.completedActions.length > 0 && (
            <Card className="tron-card">
              <CardHeader>
                <CardTitle className="text-primary">Completed Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {status.completedActions.map((action, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 border border-primary/20 rounded">
                      <FiCheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      <span className="text-foreground text-sm">{action}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Errors */}
          {status.errors.length > 0 && (
            <Card className="tron-card border-red-500/50">
              <CardHeader>
                <CardTitle className="text-red-500">Errors Encountered</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {status.errors.map((error, index) => (
                    <div key={index} className="p-2 bg-red-500/10 border border-red-500/30 rounded">
                      <span className="text-red-400 text-sm">{error}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default TronBacklogSweeperScreen;
