import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  FiArrowLeft, 
  FiCheckSquare, 
  FiSearch,
  FiAlertTriangle,
  FiCheckCircle,
  FiLoader,
  FiFilter,
  FiList,
  FiFolder,
  FiFileText
} from 'react-icons/fi';

interface TestCase {
  id: number;
  title: string;
  state: string;
  areaPath: string;
  testSuite?: string;
}

interface TestSuite {
  id: number;
  name: string;
  testCaseCount: number;
}

interface TestPlan {
  id: number;
  name: string;
  state: string;
  testSuiteCount: number;
}

const TronCleanupTestCasesScreen: React.FC = () => {
  const navigate = useNavigate();
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [testPlans, setTestPlans] = useState<TestPlan[]>([]);
  
  const [selectedTestCases, setSelectedTestCases] = useState<number[]>([]);
  const [selectedTestSuites, setSelectedTestSuites] = useState<number[]>([]);
  const [selectedTestPlans, setSelectedTestPlans] = useState<number[]>([]);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteProgress, setDeleteProgress] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState('testcases');

  useEffect(() => {
    loadTestData();
  }, []);

  const loadTestData = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const [casesResponse, suitesResponse, plansResponse] = await Promise.all([
        fetch('/api/testcases'),
        fetch('/api/testsuites'),
        fetch('/api/testplans')
      ]);

      if (casesResponse.ok && suitesResponse.ok && plansResponse.ok) {
        const [casesData, suitesData, plansData] = await Promise.all([
          casesResponse.json(),
          suitesResponse.json(),
          plansResponse.json()
        ]);

        setTestCases(casesData);
        setTestSuites(suitesData);
        setTestPlans(plansData);
        
        setMessage({ 
          type: 'info', 
          text: `Loaded ${casesData.length} test cases, ${suitesData.length} suites, ${plansData.length} plans` 
        });
      } else {
        setMessage({ type: 'error', text: 'Failed to load test data' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error connecting to Azure DevOps Test API' });
    } finally {
      setLoading(false);
    }
  };

  const deleteSelectedItems = async () => {
    const hasSelections = selectedTestCases.length > 0 || selectedTestSuites.length > 0 || selectedTestPlans.length > 0;
    if (!hasSelections) return;

    setDeleting(true);
    setDeleteProgress(0);
    
    try {
      const response = await fetch('/api/test/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          testCases: selectedTestCases,
          testSuites: selectedTestSuites,
          testPlans: selectedTestPlans
        })
      });

      if (response.ok) {
        // Simulate progress updates
        for (let i = 0; i <= 100; i += 10) {
          setDeleteProgress(i);
          await new Promise(resolve => setTimeout(resolve, 300));
        }
        
        const totalDeleted = selectedTestCases.length + selectedTestSuites.length + selectedTestPlans.length;
        setMessage({ type: 'success', text: `Successfully deleted ${totalDeleted} test items` });
        
        setSelectedTestCases([]);
        setSelectedTestSuites([]);
        setSelectedTestPlans([]);
        
        loadTestData(); // Refresh the lists
      } else {
        setMessage({ type: 'error', text: 'Failed to delete test items' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error during deletion process' });
    } finally {
      setDeleting(false);
      setDeleteProgress(0);
    }
  };

  const toggleSelectAllTestCases = () => {
    const filtered = filteredTestCases;
    if (selectedTestCases.length === filtered.length) {
      setSelectedTestCases([]);
    } else {
      setSelectedTestCases(filtered.map(item => item.id));
    }
  };

  const toggleSelectAllTestSuites = () => {
    const filtered = filteredTestSuites;
    if (selectedTestSuites.length === filtered.length) {
      setSelectedTestSuites([]);
    } else {
      setSelectedTestSuites(filtered.map(item => item.id));
    }
  };

  const toggleSelectAllTestPlans = () => {
    const filtered = filteredTestPlans;
    if (selectedTestPlans.length === filtered.length) {
      setSelectedTestPlans([]);
    } else {
      setSelectedTestPlans(filtered.map(item => item.id));
    }
  };

  const filteredTestCases = testCases.filter(item => 
    item.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTestSuites = testSuites.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTestPlans = testPlans.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalSelected = selectedTestCases.length + selectedTestSuites.length + selectedTestPlans.length;

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
            <FiCheckSquare className="w-12 h-12 text-destructive pulse-glow" />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            TEST CASE <span className="text-destructive">CLEANUP</span>
          </h1>
          <p className="text-muted-foreground font-mono">
            DELETE TEST CASES, SUITES, AND PLANS
          </p>
        </div>

        {/* Controls */}
        <div className="max-w-6xl mx-auto space-y-6">
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary flex items-center">
                <FiFilter className="w-5 h-5 mr-2" />
                Search and Controls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <Label htmlFor="search" className="text-foreground">Search Test Items</Label>
                  <div className="relative">
                    <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="search"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Search by name or title..."
                      className="tron-input pl-10"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={loadTestData}
                  disabled={loading}
                  className="tron-button"
                >
                  {loading ? <FiLoader className="w-4 h-4 mr-2 animate-spin" /> : <FiSearch className="w-4 h-4 mr-2" />}
                  {loading ? 'SCANNING...' : 'SCAN TEST DATA'}
                </Button>

                <Button
                  onClick={deleteSelectedItems}
                  disabled={totalSelected === 0 || deleting}
                  variant="destructive"
                  className="bg-destructive hover:bg-destructive/90"
                >
                  {deleting ? <FiLoader className="w-4 h-4 mr-2 animate-spin" /> : <FiCheckSquare className="w-4 h-4 mr-2" />}
                  DELETE SELECTED ({totalSelected})
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Progress Bar */}
          {deleting && (
            <Card className="tron-card">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-foreground">Deletion Progress</span>
                    <span className="text-primary">{deleteProgress}%</span>
                  </div>
                  <Progress value={deleteProgress} className="h-2" />
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
               message.type === 'error' ? <FiAlertTriangle className="h-4 w-4 text-red-500" /> :
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

          {/* Test Items Tabs */}
          <Card className="tron-card">
            <CardContent className="pt-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3 bg-card/50 border border-primary/30">
                  <TabsTrigger 
                    value="testcases" 
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    <FiFileText className="w-4 h-4 mr-2" />
                    Test Cases ({filteredTestCases.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="testsuites" 
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    <FiFolder className="w-4 h-4 mr-2" />
                    Test Suites ({filteredTestSuites.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="testplans" 
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    <FiList className="w-4 h-4 mr-2" />
                    Test Plans ({filteredTestPlans.length})
                  </TabsTrigger>
                </TabsList>

                {/* Test Cases Tab */}
                <TabsContent value="testcases">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold text-foreground">Test Cases</h3>
                      <Button
                        onClick={toggleSelectAllTestCases}
                        disabled={filteredTestCases.length === 0}
                        variant="outline"
                        className="border-primary/50 text-primary hover:bg-primary/10"
                      >
                        {selectedTestCases.length === filteredTestCases.length ? 'DESELECT ALL' : 'SELECT ALL'}
                      </Button>
                    </div>
                    
                    {filteredTestCases.length === 0 ? (
                      <div className="text-center py-12 text-muted-foreground">
                        {loading ? 'Scanning for test cases...' : 'No test cases found'}
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {filteredTestCases.map(testCase => (
                          <div
                            key={testCase.id}
                            className={`flex items-center space-x-4 p-3 rounded-lg border transition-all duration-200 ${
                              selectedTestCases.includes(testCase.id)
                                ? 'border-primary bg-primary/10'
                                : 'border-primary/20 hover:border-primary/40'
                            }`}
                          >
                            <Checkbox
                              checked={selectedTestCases.includes(testCase.id)}
                              onCheckedChange={() => {
                                setSelectedTestCases(prev => 
                                  prev.includes(testCase.id) 
                                    ? prev.filter(id => id !== testCase.id)
                                    : [...prev, testCase.id]
                                );
                              }}
                              className="border-primary"
                            />
                            
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-mono text-primary">#{testCase.id}</span>
                                <span className="font-semibold text-foreground">{testCase.title}</span>
                              </div>
                              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                                <span>State: {testCase.state}</span>
                                <span>Area: {testCase.areaPath}</span>
                                {testCase.testSuite && <span>Suite: {testCase.testSuite}</span>}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Test Suites Tab */}
                <TabsContent value="testsuites">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold text-foreground">Test Suites</h3>
                      <Button
                        onClick={toggleSelectAllTestSuites}
                        disabled={filteredTestSuites.length === 0}
                        variant="outline"
                        className="border-primary/50 text-primary hover:bg-primary/10"
                      >
                        {selectedTestSuites.length === filteredTestSuites.length ? 'DESELECT ALL' : 'SELECT ALL'}
                      </Button>
                    </div>
                    
                    {filteredTestSuites.length === 0 ? (
                      <div className="text-center py-12 text-muted-foreground">
                        {loading ? 'Scanning for test suites...' : 'No test suites found'}
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {filteredTestSuites.map(suite => (
                          <div
                            key={suite.id}
                            className={`flex items-center space-x-4 p-3 rounded-lg border transition-all duration-200 ${
                              selectedTestSuites.includes(suite.id)
                                ? 'border-primary bg-primary/10'
                                : 'border-primary/20 hover:border-primary/40'
                            }`}
                          >
                            <Checkbox
                              checked={selectedTestSuites.includes(suite.id)}
                              onCheckedChange={() => {
                                setSelectedTestSuites(prev => 
                                  prev.includes(suite.id) 
                                    ? prev.filter(id => id !== suite.id)
                                    : [...prev, suite.id]
                                );
                              }}
                              className="border-primary"
                            />
                            
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-mono text-primary">#{suite.id}</span>
                                <span className="font-semibold text-foreground">{suite.name}</span>
                              </div>
                              <div className="text-sm text-muted-foreground">
                                Test Cases: {suite.testCaseCount}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Test Plans Tab */}
                <TabsContent value="testplans">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold text-foreground">Test Plans</h3>
                      <Button
                        onClick={toggleSelectAllTestPlans}
                        disabled={filteredTestPlans.length === 0}
                        variant="outline"
                        className="border-primary/50 text-primary hover:bg-primary/10"
                      >
                        {selectedTestPlans.length === filteredTestPlans.length ? 'DESELECT ALL' : 'SELECT ALL'}
                      </Button>
                    </div>
                    
                    {filteredTestPlans.length === 0 ? (
                      <div className="text-center py-12 text-muted-foreground">
                        {loading ? 'Scanning for test plans...' : 'No test plans found'}
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {filteredTestPlans.map(plan => (
                          <div
                            key={plan.id}
                            className={`flex items-center space-x-4 p-3 rounded-lg border transition-all duration-200 ${
                              selectedTestPlans.includes(plan.id)
                                ? 'border-primary bg-primary/10'
                                : 'border-primary/20 hover:border-primary/40'
                            }`}
                          >
                            <Checkbox
                              checked={selectedTestPlans.includes(plan.id)}
                              onCheckedChange={() => {
                                setSelectedTestPlans(prev => 
                                  prev.includes(plan.id) 
                                    ? prev.filter(id => id !== plan.id)
                                    : [...prev, plan.id]
                                );
                              }}
                              className="border-primary"
                            />
                            
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-mono text-primary">#{plan.id}</span>
                                <span className="font-semibold text-foreground">{plan.name}</span>
                              </div>
                              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                                <span>State: {plan.state}</span>
                                <span>Test Suites: {plan.testSuiteCount}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Warning */}
          <Alert className="border-red-500/50 bg-red-500/10">
            <FiAlertTriangle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-red-400">
              <strong>WARNING:</strong> This action cannot be undone. Selected test cases, suites, and plans will be permanently deleted from Azure DevOps.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    </div>
  );
};

export default TronCleanupTestCasesScreen;
