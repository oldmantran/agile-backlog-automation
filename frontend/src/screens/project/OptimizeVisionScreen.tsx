import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Sparkles, AlertCircle, ChevronRight, Check, Loader2 } from 'lucide-react';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import apiClient from '../../services/api/apiClient';

interface Domain {
  id: number;
  domain_key: string;
  display_name: string;
  description: string;
}

interface VisionOptimizationResult {
  vision_id?: number;
  optimized_vision: string;
  original_score: number;
  optimized_score: number;
  score_improvement: number;
  rating_change: string;
  improvements_made: string[];
  remaining_issues: string[];
  is_acceptable: boolean;
}

const OptimizeVisionScreen: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [visionStatement, setVisionStatement] = useState('');
  
  // Simple toast function
  const toast = (options: { title: string; description?: string; variant?: 'default' | 'destructive' }) => {
    setNotification({
      message: options.description || options.title,
      type: options.variant === 'destructive' ? 'error' : 'success'
    });
    // Auto-hide after 5 seconds
    setTimeout(() => setNotification(null), 5000);
  };
  const [selectedDomains, setSelectedDomains] = useState<Array<{ domain: string; priority: string }>>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<VisionOptimizationResult | null>(null);
  const [availableDomains, setAvailableDomains] = useState<Domain[]>([]);
  const [isCheckingQuality, setIsCheckingQuality] = useState(false);
  const [visionQuality, setVisionQuality] = useState<any>(null);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      const response = await apiClient.get('/domains');
      // Handle both response formats
      const domains = response.data.success ? response.data.data : response.data;
      setAvailableDomains(domains || []);
    } catch (error) {
      console.error('Failed to fetch domains:', error);
      setNotification({
        message: 'Unable to load domain list. Please refresh the page.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
    }
  };

  const checkVisionQuality = async () => {
    if (!visionStatement.trim()) {
      setNotification({
        message: 'Please enter a vision statement to check its quality.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
      return;
    }

    setIsCheckingQuality(true);
    try {
      const response = await apiClient.post('/api/vision/quality-check', {
        visionStatement,
        domain: selectedDomains[0]?.domain || 'general'
      });

      if (response.data.success) {
        setVisionQuality(response.data.data);
      }
    } catch (error) {
      console.error('Quality check failed:', error);
      setNotification({
        message: 'Unable to assess vision quality. Please try again.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
    } finally {
      setIsCheckingQuality(false);
    }
  };

  const handleDomainSelect = (domainKey: string) => {
    const existingIndex = selectedDomains.findIndex(d => d.domain === domainKey);
    
    if (existingIndex >= 0) {
      // Remove domain
      setSelectedDomains(selectedDomains.filter(d => d.domain !== domainKey));
    } else {
      // Add domain
      if (selectedDomains.length < 3) {
        const newDomains = [...selectedDomains, { domain: domainKey, priority: getDomainPriority(selectedDomains.length) }];
        setSelectedDomains(newDomains);
      } else {
        setNotification({
          message: 'You can select up to 3 domains.',
          type: 'error'
        });
        setTimeout(() => setNotification(null), 3000);
      }
    }
  };

  const getDomainPriority = (index: number): string => {
    if (index === 0) return 'primary';
    if (index === 1) return 'secondary';
    if (index === 2) return 'tertiary';
    return 'primary';
  };

  const getDomainRank = (index: number) => {
    if (index === 0) return 'Primary Focus';
    if (index === 1) return 'Supporting Elements';
    if (index === 2) return 'Minor Considerations';
    return '';
  };

  const getDomainDescription = (index: number) => {
    if (index === 0) return 'Main industry focus and requirements';
    if (index === 1) return 'Important integrations and compliance';
    if (index === 2) return 'Additional aspects where relevant';
    return '';
  };

  const handleOptimize = async () => {
    if (!visionStatement.trim()) {
      setNotification({
        message: 'Please enter a vision statement to optimize.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
      return;
    }

    if (selectedDomains.length === 0) {
      setNotification({
        message: 'Please select at least one domain.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
      return;
    }

    setIsOptimizing(true);
    try {
      const response = await apiClient.post('/api/vision/optimize', {
        original_vision: visionStatement,
        domains: selectedDomains
      });

      // Handle both response formats
      const result = response.data.success ? response.data.data : response.data;
      if (result) {
        setOptimizationResult(result);
        setNotification({
          message: `Vision quality improved from ${result.original_score} to ${result.optimized_score}`,
          type: 'success'
        });
        setTimeout(() => setNotification(null), 5000);
      }
    } catch (error: any) {
      console.error('Optimization failed:', error);
      setNotification({
        message: error.response?.data?.detail || 'Unable to optimize vision. Please try again.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 5000);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApproveAndCreate = () => {
    if (optimizationResult?.optimized_vision) {
      // Navigate to simple project wizard with pre-filled vision and domains
      navigate('/simple-project-wizard', {
        state: {
          prefillData: {
            visionStatement: optimizationResult.optimized_vision,
            selectedDomains: selectedDomains.map(d => d.domain),
            optimizedVisionId: optimizationResult.vision_id
          }
        }
      });
    }
  };

  return (
    <div className="min-h-screen">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="ml-0 lg:ml-[250px] pt-[70px] transition-all duration-300 ease-in-out">
        <div className="min-h-screen bg-background tron-grid relative overflow-hidden p-6">
          {/* Notification */}
          {notification && (
            <div className={`fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg ${
              notification.type === 'error' ? 'bg-red-500' : 'bg-green-500'
            } text-white`}>
              {notification.message}
            </div>
          )}
          
          <div className="max-w-6xl mx-auto">
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-primary mb-2 flex items-center gap-3">
                <Sparkles className="w-10 h-10" />
                Vision Optimization Studio
              </h1>
              <p className="text-muted-foreground text-lg">
                Transform your product vision into a foundation for EXCELLENT quality work items
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Section */}
              <div className="space-y-6">
                {/* Vision Input */}
                <Card className="tron-card">
                  <CardHeader>
                    <CardTitle>Original Vision Statement</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={visionStatement}
                      onChange={(e) => setVisionStatement(e.target.value)}
                      placeholder="Paste your product vision statement here..."
                      className="min-h-[200px] resize-none"
                    />
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        {visionStatement.split(' ').filter(w => w).length} words
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={checkVisionQuality}
                        disabled={isCheckingQuality || !visionStatement.trim()}
                      >
                        {isCheckingQuality ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Checking...
                          </>
                        ) : (
                          'Check Quality'
                        )}
                      </Button>
                    </div>

                    {visionQuality && (
                      <Alert className={visionQuality.is_acceptable ? 'border-green-500' : 'border-orange-500'}>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold">Quality Score: {visionQuality.score}/100</span>
                              <Badge variant={visionQuality.is_acceptable ? 'default' : 'secondary'}>
                                {visionQuality.rating}
                              </Badge>
                            </div>
                            <Progress value={visionQuality.score} className="h-2" />
                            {!visionQuality.is_acceptable && (
                              <p className="text-sm">
                                Minimum score of 75 required. Optimization recommended.
                              </p>
                            )}
                          </div>
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>

                {/* Domain Selection */}
                <Card className="tron-card">
                  <CardHeader>
                    <CardTitle>Select Domains (Up to 3)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                          <AlertCircle className="w-4 h-4" />
                          <span>Select up to 3 domains. Click to add/remove. First selected becomes primary.</span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {selectedDomains.length}/3 selected
                        </div>
                      </div>
                      
                      <div className="relative" style={{ maxHeight: '320px' }}>
                        <div className="overflow-y-auto overflow-x-hidden pr-2" style={{ maxHeight: '320px', scrollbarWidth: 'thin' }}>
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {availableDomains.map((domain) => {
                        const isSelected = selectedDomains.some(d => d.domain === domain.domain_key);
                        const domainIndex = selectedDomains.findIndex(d => d.domain === domain.domain_key);
                        const isPrimary = domainIndex === 0;
                        
                        return (
                          <div
                            key={domain.id}
                            onClick={() => handleDomainSelect(domain.domain_key)}
                            className={`
                              relative p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:scale-105
                              ${isSelected 
                                ? isPrimary 
                                  ? 'border-primary bg-primary/20 shadow-lg' 
                                  : 'border-secondary bg-secondary/20 shadow-md'
                                : 'border-border bg-background hover:border-muted-foreground'
                              }
                              ${selectedDomains.length >= 3 && !isSelected ? 'opacity-50 cursor-not-allowed' : ''}
                            `}
                          >
                            <div className="text-sm font-medium text-foreground truncate">
                              {domain.display_name}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {domain.description}
                            </div>
                            {isSelected && (
                              <div className="absolute top-2 right-2">
                                <Badge 
                                  variant={isPrimary ? "default" : "secondary"} 
                                  className="text-xs"
                                >
                                  {getDomainRank(domainIndex)}
                                </Badge>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                        </div>
                      </div>
                    </div>

                    {selectedDomains.length > 0 && (
                      <div className="mt-4 space-y-3">
                        <Label className="text-base font-semibold">Domain Integration Strategy</Label>
                        {selectedDomains.map((domain, index) => (
                          <div key={domain.domain} className="p-3 rounded-lg bg-muted/50 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">
                                {availableDomains.find(d => d.domain_key === domain.domain)?.display_name}
                              </span>
                              <Badge 
                                variant={index === 0 ? "default" : "secondary"}
                                className="text-xs"
                              >
                                {getDomainRank(index)}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {getDomainDescription(index)}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Optimize Button */}
                <Button
                  className="w-full"
                  size="lg"
                  onClick={handleOptimize}
                  disabled={isOptimizing || !visionStatement.trim() || selectedDomains.length === 0}
                >
                  {isOptimizing ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Optimizing Vision...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      Optimize Vision
                    </>
                  )}
                </Button>
              </div>

              {/* Results Section */}
              <div>
                {optimizationResult ? (
                  <Card className="tron-card">
                    <CardHeader>
                      <CardTitle>Optimization Results</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {/* Score Improvement */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Quality Improvement</span>
                          <span className="text-2xl font-bold text-primary">
                            +{optimizationResult.score_improvement}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">{optimizationResult.rating_change.split(' → ')[0]}</Badge>
                          <ChevronRight className="h-4 w-4" />
                          <Badge variant="default">{optimizationResult.rating_change.split(' → ')[1]}</Badge>
                        </div>
                      </div>

                      {/* Improvements Made */}
                      {optimizationResult.improvements_made.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Improvements Made</h4>
                          <ul className="space-y-1">
                            {optimizationResult.improvements_made.map((improvement, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm">
                                <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                <span>{improvement}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Optimized Vision */}
                      <div>
                        <h4 className="font-medium mb-2">Optimized Vision</h4>
                        <div className="bg-muted/50 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                          <p className="text-sm whitespace-pre-wrap">{optimizationResult.optimized_vision}</p>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        <Button
                          className="flex-1"
                          onClick={handleApproveAndCreate}
                          disabled={!optimizationResult.is_acceptable}
                        >
                          Approve & Create New Backlog
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setVisionStatement(optimizationResult.optimized_vision);
                            setOptimizationResult(null);
                          }}
                        >
                          Use as New Input
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="tron-card h-full flex items-center justify-center">
                    <CardContent className="text-center py-12">
                      <Sparkles className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-xl font-semibold mb-2">Ready to Optimize</h3>
                      <p className="text-muted-foreground">
                        Enter your vision statement, select domains, and click Optimize to begin
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptimizeVisionScreen;