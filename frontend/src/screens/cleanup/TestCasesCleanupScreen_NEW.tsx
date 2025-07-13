import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Separator } from '../../components/ui/separator';
import { Progress } from '../../components/ui/progress';
import { Checkbox } from '../../components/ui/checkbox';
import { FiClipboard, FiAlertTriangle, FiArrowLeft, FiPlay, FiInfo } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface TestCaseStats {
  totalTestCases: number;
  gritAreaCases: number;
  dataVizAreaCases: number;
}

const TestCasesCleanupScreen: React.FC = () => {
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(false);
  const [isDryRun, setIsDryRun] = useState(true);
  const [projectName, setProjectName] = useState('Backlog Automation');
  const [areaPaths, setAreaPaths] = useState('Backlog Automation\\Grit\nBacklog Automation\\Data Visualization');
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [cleanupStats, setCleanupStats] = useState<TestCaseStats | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleCleanup = async () => {
    setIsLoading(true);
    setProgress(0);
    setCurrentOperation('Initializing test case cleanup...');

    try {
      await simulateTestCaseCleanup();
      setIsComplete(true);
      console.log(`Test Case Cleanup Complete: Successfully ${isDryRun ? 'simulated cleanup of' : 'cleaned'} test cases using Test Management API`);
    } catch (error) {
      console.error('Cleanup Failed: An error occurred during the test case cleanup process');
    } finally {
      setIsLoading(false);
    }
  };

  const simulateTestCaseCleanup = async () => {
    const steps = [
      'Authenticating with Azure DevOps...',
      'Fetching test cases from Grit area path...',
      'Fetching test cases from Data Visualization area path...',
      'Analyzing dependencies...',
      'Processing cleanup operations...',
      'Finalizing cleanup process...'
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentOperation(steps[i]);
      setProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setCleanupStats({
      totalTestCases: 654,
      gritAreaCases: 248,
      dataVizAreaCases: 406
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
            <FiClipboard className="w-6 h-6" />
            <h1 className="text-3xl font-bold">Test Cases Cleanup</h1>
          </div>
        </div>

        <p className="text-muted-foreground">
          Remove test cases from Azure DevOps using the Test Management API. 
          This cleanup tool specifically targets test cases in the specified area paths.
        </p>

        <Alert variant="destructive">
          <FiAlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <div>
              <strong>Special Requirements for Test Cases!</strong>
              <p className="mt-1">
                Test cases require special API endpoints and permissions in Azure DevOps. 
                Ensure you have Test Plans management permissions.
              </p>
            </div>
          </AlertDescription>
        </Alert>

        <Alert>
          <FiInfo className="w-4 h-4" />
          <AlertDescription>
            <div>
              <strong>API Difference</strong>
              <p className="mt-1">
                This cleanup uses the <code className="bg-muted px-1 py-0.5 rounded text-sm">/test/testcases</code> endpoint instead of the{' '}
                <code className="bg-muted px-1 py-0.5 rounded text-sm">/wit/workitems</code> endpoint.
              </p>
            </div>
          </AlertDescription>
        </Alert>

        <Card>
          <CardHeader>
            <CardTitle>Test Case Cleanup Configuration</CardTitle>
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
                  Enter one area path per line. These paths will be searched for test cases to clean.
                </p>
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
                    Preview changes without actually deleting test cases
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
                <CardTitle className="text-green-600">Last Test Case Cleanup Results</CardTitle>
                <Badge variant="default" className="bg-green-100 text-green-800">SUCCESS</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Cleanup completed successfully on {new Date().toLocaleDateString()}
                </p>
                <div className="flex justify-between">
                  <span>Total Test Cases Deleted:</span>
                  <span className="font-bold text-green-600">654</span>
                </div>
                <div className="flex justify-between">
                  <span>• From Grit area path:</span>
                  <span>248</span>
                </div>
                <div className="flex justify-between">
                  <span>• From Data Visualization area path:</span>
                  <span>406</span>
                </div>
                <Separator />
                <p className="text-sm text-muted-foreground flex items-center">
                  <FiInfo className="w-4 h-4 mr-2" />
                  Used Test Management API endpoint: <code className="bg-muted px-1 py-0.5 rounded text-xs ml-1">/test/testcases</code>
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="border-blue-200 border">
          <CardHeader>
            <CardTitle className="text-blue-600 text-sm">Technical Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <p>
                <strong>API Endpoint:</strong> <code className="bg-muted px-1 py-0.5 rounded">DELETE /test/testcases/&#123;id&#125;</code>
              </p>
              <p>
                <strong>API Version:</strong> <code className="bg-muted px-1 py-0.5 rounded">7.1-preview.1</code>
              </p>
              <p>
                <strong>Required Permissions:</strong> Test Plans (Read & Write), Test Management
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
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Total Test Cases:</span>
                        <span className="font-bold">{cleanupStats.totalTestCases}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>• From Grit area:</span>
                        <span>{cleanupStats.gritAreaCases}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>• From Data Visualization area:</span>
                        <span>{cleanupStats.dataVizAreaCases}</span>
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

export default TestCasesCleanupScreen;
