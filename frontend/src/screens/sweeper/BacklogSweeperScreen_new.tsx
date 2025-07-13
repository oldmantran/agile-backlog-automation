import React, { useState } from 'react';
import { 
  FiRefreshCw, 
  FiArrowLeft, 
  FiPlay, 
  FiSettings, 
  FiCheckCircle, 
  FiClock,
  FiUsers,
  FiTarget,
  FiTrendingUp
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Checkbox } from '../../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const BacklogSweeperScreen: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState({
    agentMode: 'automatic' as 'manual' | 'automatic',
    targetItems: 10,
    includeAcceptanceCriteria: true,
    includeTaskDecomposition: true,
    includeQualityCheck: true,
    selectedAgents: ['epic-strategist', 'user-story-decomposer', 'qa-lead'],
  });

  const handleRunSweeper = async () => {
    setIsLoading(true);
    try {
      console.log('Running backlog sweeper with config:', config);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      alert('Backlog sweeper completed successfully!');
    } catch (error) {
      console.error('Backlog sweeper failed:', error);
      alert('Backlog sweeper failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Convert Chakra UI Box p={6} to Tailwind p-6
    <div className="p-6">
      {/* Convert Chakra UI VStack spacing={6} align="stretch" to Tailwind space-y-6 w-full */}
      <div className="space-y-6 w-full">
        {/* Header - Convert HStack to flex items-center */}
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2"
          >
            <FiArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-bold mb-2 text-green-500 flex items-center">
            <FiRefreshCw className="mr-3 h-6 w-6" />
            Backlog Sweeper
          </h1>
          <p className="text-muted-foreground">
            Automated backlog enhancement with AI-powered quality improvements
          </p>
        </div>

        {/* Info Alert */}
        <Alert className="border-cyan-500/30 bg-cyan-950/30">
          <AlertDescription className="text-cyan-100">
            <div>
              <div className="font-semibold mb-1">Intelligent Backlog Enhancement</div>
              <div>
                The backlog sweeper uses AI agents to automatically improve your backlog items with 
                better acceptance criteria, task decomposition, and quality checks.
              </div>
            </div>
          </AlertDescription>
        </Alert>

        {/* Configuration Section */}
        <Card className="shadow-lg border-cyan-500/20">
          <CardHeader>
            <CardTitle className="text-cyan-100">Sweeper Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Agent Mode */}
            <div className="space-y-2">
              <Label className="text-cyan-100">Agent Mode</Label>
              <Select value={config.agentMode} onValueChange={(value) => 
                setConfig(prev => ({ ...prev, agentMode: value as 'manual' | 'automatic' }))
              }>
                <SelectTrigger className="bg-slate-800/50 border-cyan-500/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="automatic">Automatic Mode</SelectItem>
                  <SelectItem value="manual">Manual Review Mode</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Target Items */}
            <div className="space-y-2">
              <Label className="text-cyan-100">Target Items Count</Label>
              <Input
                type="number"
                value={config.targetItems}
                onChange={(e) => setConfig(prev => ({ ...prev, targetItems: parseInt(e.target.value) }))}
                className="bg-slate-800/50 border-cyan-500/30 text-cyan-100"
              />
            </div>

            {/* Enhancement Options */}
            <div className="space-y-3">
              <Label className="text-cyan-100">Enhancement Options</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={config.includeAcceptanceCriteria}
                    onCheckedChange={(checked) => 
                      setConfig(prev => ({ ...prev, includeAcceptanceCriteria: !!checked }))
                    }
                  />
                  <Label className="text-cyan-100">Include Acceptance Criteria Enhancement</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={config.includeTaskDecomposition}
                    onCheckedChange={(checked) => 
                      setConfig(prev => ({ ...prev, includeTaskDecomposition: !!checked }))
                    }
                  />
                  <Label className="text-cyan-100">Include Task Decomposition</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={config.includeQualityCheck}
                    onCheckedChange={(checked) => 
                      setConfig(prev => ({ ...prev, includeQualityCheck: !!checked }))
                    }
                  />
                  <Label className="text-cyan-100">Include Quality Checks</Label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Available Agents */}
        <Card className="shadow-lg border-cyan-500/20">
          <CardHeader>
            <CardTitle className="text-cyan-100">Available AI Agents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3">
              <div className="flex items-center justify-between p-3 border border-cyan-500/30 rounded-lg bg-slate-800/30">
                <div className="flex items-center space-x-3">
                  <FiUsers className="h-5 w-5 text-cyan-400" />
                  <div>
                    <div className="font-medium text-cyan-100">Epic Strategist</div>
                    <div className="text-sm text-cyan-400">Enhances epic-level planning</div>
                  </div>
                </div>
                <Badge className="bg-green-600 text-white">Active</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 border border-cyan-500/30 rounded-lg bg-slate-800/30">
                <div className="flex items-center space-x-3">
                  <FiTarget className="h-5 w-5 text-cyan-400" />
                  <div>
                    <div className="font-medium text-cyan-100">User Story Decomposer</div>
                    <div className="text-sm text-cyan-400">Breaks down complex stories</div>
                  </div>
                </div>
                <Badge className="bg-green-600 text-white">Active</Badge>
              </div>

              <div className="flex items-center justify-between p-3 border border-cyan-500/30 rounded-lg bg-slate-800/30">
                <div className="flex items-center space-x-3">
                  <FiCheckCircle className="h-5 w-5 text-cyan-400" />
                  <div>
                    <div className="font-medium text-cyan-100">QA Lead Agent</div>
                    <div className="text-sm text-cyan-400">Quality assurance and testing</div>
                  </div>
                </div>
                <Badge className="bg-green-600 text-white">Active</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons - Convert HStack to flex items-center space-x-4 */}
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleRunSweeper}
            disabled={isLoading}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white"
          >
            <FiPlay className="h-4 w-4" />
            {isLoading ? 'Running Sweeper...' : 'Run Backlog Sweeper'}
          </Button>
          
          <Button
            variant="outline"
            onClick={() => navigate('/settings')}
            disabled={isLoading}
            className="flex items-center gap-2 border-cyan-500/30 text-cyan-100 hover:bg-cyan-500/10"
          >
            <FiSettings className="h-4 w-4" />
            Advanced Settings
          </Button>
          
          <Button
            variant="outline"
            onClick={() => navigate('/dashboard')}
            disabled={isLoading}
            className="border-cyan-500/30 text-cyan-100 hover:bg-cyan-500/10"
          >
            Cancel
          </Button>
        </div>

        {/* Progress indicator when loading */}
        {isLoading && (
          <Card className="shadow-lg border-cyan-500/20">
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <FiClock className="h-5 w-5 text-cyan-400 animate-spin" />
                  <span className="text-cyan-100 font-medium">Processing backlog items...</span>
                </div>
                <Progress value={33} className="w-full" />
                <p className="text-sm text-cyan-400">
                  Analyzing {config.targetItems} backlog items with selected AI agents...
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default BacklogSweeperScreen;
