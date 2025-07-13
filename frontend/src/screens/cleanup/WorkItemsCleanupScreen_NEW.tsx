import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Separator } from '../../components/ui/separator';
import { Progress } from '../../components/ui/progress';
import { Checkbox } from '../../components/ui/checkbox';
import { FiTrash2, FiAlertTriangle, FiArrowLeft, FiPlay } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface CleanupStats {
  totalItems: number;
  epics: number;
  features: number;
  userStories: number;
  tasks: number;
  bugs: number;
}

const WorkItemsCleanupScreen: React.FC = () => {
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(false);
  const [isDryRun, setIsDryRun] = useState(true);
  const [projectName, setProjectName] = useState('Backlog Automation');
  const [areaPaths, setAreaPaths] = useState('Backlog Automation\\Grit\nBacklog Automation\\Data Visualization');
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [cleanupStats, setCleanupStats] = useState<CleanupStats | null>(null);
  const [workItemType, setWorkItemType] = useState('all');
  const [isComplete, setIsComplete] = useState(false);

  const handleCleanup = async () => {
    setIsLoading(true);
    setProgress(0);
    setCurrentOperation('Initializing work item cleanup...');

    try {
      await simulateCleanup();
      setIsComplete(true);
      console.log(`Work Item Cleanup Complete: Successfully ${isDryRun ? 'simulated cleanup of' : 'cleaned'} work items`);
    } catch (error) {
      console.error('Cleanup Failed: An error occurred during the cleanup process');
    } finally {
      setIsLoading(false);
    }
  };

  const simulateCleanup = async () => {
    const steps = [
      'Authenticating with Azure DevOps...',
      'Fetching work items from area paths...',
      'Analyzing dependencies and relationships...',
      'Processing cleanup operations...',
      'Updating work item states...',
      'Finalizing cleanup process...'
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentOperation(steps[i]);
      setProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, 1500));
    }

    setCleanupStats({
      totalItems: 342,
      epics: 12,
      features: 34,
      userStories: 156,
      tasks: 98,
      bugs: 42
    });
  };

  const resetCleanup = () => {
    setIsComplete(false);
    setProgress(0);
    setCurrentOperation('');
    setCleanupStats(null);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center space-x-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            <FiArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <div className="flex items-center space-x-2">
            <FiTrash2 className="w-6 h-6" />
            <h1 className="text-3xl font-bold">Work Items Cleanup</h1>
          </div>
        </div>

        <p className="text-muted-foreground">
          Remove work items from Azure DevOps based on area path filtering. 
          This tool helps clean up orphaned or unwanted work items from your project.
        </p>

        <Alert variant="destructive">
          <FiAlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <div>
              <strong>Warning:</strong> This action will permanently delete work items from Azure DevOps.
              Always run in dry-run mode first to preview what will be deleted.
            </div>
          </AlertDescription>
        </Alert>

        <Card>
          <CardHeader>
            <CardTitle>Cleanup Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="projectName">Azure DevOps Project</Label>
                <Input
                  id="projectName"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="areaPaths">Area Paths to Clean</Label>
                <Textarea
                  id="areaPaths"
                  value={areaPaths}
                  onChange={(e) => setAreaPaths(e.target.value)}
                  placeholder="Enter area paths (one per line)"
                  rows={3}
                />
                <p className="text-sm text-muted-foreground">
                  Enter one area path per line. Work items under these paths will be processed.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="workItemType">Work Item Type Filter</Label>
                <Select value={workItemType} onValueChange={setWorkItemType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select work item type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="Epic">Epics Only</SelectItem>
                    <SelectItem value="Feature">Features Only</SelectItem>
                    <SelectItem value="User Story">User Stories Only</SelectItem>
                    <SelectItem value="Task">Tasks Only</SelectItem>
                    <SelectItem value="Bug">Bugs Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="dryRun"
                  checked={isDryRun}
                  onCheckedChange={(checked) => setIsDryRun(checked as boolean)}
                />
                <div>
                  <Label htmlFor="dryRun" className="font-medium">Dry Run Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Preview changes without actually deleting work items
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {isComplete && (
          <Card className="border-green-200 border-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-green-600">Last Cleanup Results</CardTitle>
                <Badge variant="default" className="bg-green-100 text-green-800">SUCCESS</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Cleanup completed successfully on {new Date().toLocaleDateString()}
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex justify-between">
                    <span>Total Items:</span>
                    <span className="font-bold text-green-600">{cleanupStats?.totalItems}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Epics:</span>
                    <span>{cleanupStats?.epics}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Features:</span>
                    <span>{cleanupStats?.features}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>User Stories:</span>
                    <span>{cleanupStats?.userStories}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tasks:</span>
                    <span>{cleanupStats?.tasks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Bugs:</span>
                    <span>{cleanupStats?.bugs}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="border-blue-200 border">
          <CardHeader>
            <CardTitle className="text-blue-600 text-sm">API Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <p>
                <strong>Endpoint:</strong> <code className="bg-muted px-1 py-0.5 rounded">DELETE /wit/workitems/&#123;id&#125;</code>
              </p>
              <p>
                <strong>API Version:</strong> <code className="bg-muted px-1 py-0.5 rounded">7.1-preview.3</code>
              </p>
              <p>
                <strong>Required Permissions:</strong> Work Items (Read & Write)
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex space-x-4">
          <Button
            onClick={handleCleanup}
            size="lg"
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            <FiPlay className="w-4 h-4" />
            <span>
              {isLoading
                ? 'Processing...'
                : isDryRun
                ? 'Preview Cleanup'
                : 'Start Cleanup'}
            </span>
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={resetCleanup}
            disabled={isLoading}
          >
            Reset
          </Button>
        </div>

        {isLoading && (
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <Progress value={progress} className="w-full" />
                  <p className="text-sm text-muted-foreground mt-2">{currentOperation}</p>
                </div>
                {cleanupStats && (
                  <>
                    <Separator />
                    <div className="font-bold text-foreground">
                      {isDryRun ? 'Dry Run Results:' : 'Cleanup Results:'}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex justify-between">
                        <span>Total Items:</span>
                        <span className="font-bold">{cleanupStats.totalItems}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Epics:</span>
                        <span>{cleanupStats.epics}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Features:</span>
                        <span>{cleanupStats.features}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>User Stories:</span>
                        <span>{cleanupStats.userStories}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tasks:</span>
                        <span>{cleanupStats.tasks}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Bugs:</span>
                        <span>{cleanupStats.bugs}</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default WorkItemsCleanupScreen;
