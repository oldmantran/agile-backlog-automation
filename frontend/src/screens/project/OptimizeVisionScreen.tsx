import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Sparkles, AlertCircle, ChevronRight, Check, Loader2, History, Calendar, Award, RefreshCw, Info as FiInfo, Download } from 'lucide-react';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import apiClient from '../../services/api/apiClient';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog';

interface Domain {
  id: number;
  domain_key: string;
  display_name: string;
  description: string;
}

interface VisionAssessment {
  score: number;
  rating: string;
  strengths: string[];
  weaknesses: string[];
  missing_elements: string[];
  improvement_suggestions?: string[];
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
  original_assessment?: VisionAssessment;
  optimized_assessment?: VisionAssessment;
}

interface SavedVision {
  id: number;
  original_vision: string;
  optimized_vision: string;
  domains: Array<{ domain: string; priority: string }>;
  quality_score: number;
  quality_rating: string;
  created_at: string;
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
  const [savedVisions, setSavedVisions] = useState<SavedVision[]>([]);
  const [isLoadingVisions, setIsLoadingVisions] = useState(false);
  const [visionDialogOpen, setVisionDialogOpen] = useState(false);

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

  const fetchSavedVisions = async () => {
    setIsLoadingVisions(true);
    try {
      const response = await apiClient.get('/vision/optimized?limit=20');
      setSavedVisions(response.data || []);
    } catch (error) {
      console.error('Failed to fetch saved visions:', error);
      setNotification({
        message: 'Unable to load saved visions. Please try again.',
        type: 'error'
      });
      setTimeout(() => setNotification(null), 3000);
    } finally {
      setIsLoadingVisions(false);
    }
  };

  const handleLoadVision = (vision: SavedVision) => {
    setVisionStatement(vision.optimized_vision);
    // Parse and set domains
    const parsedDomains = typeof vision.domains === 'string' 
      ? JSON.parse(vision.domains) 
      : vision.domains;
    setSelectedDomains(parsedDomains || []);
    setVisionDialogOpen(false);
    setNotification({
      message: 'Saved vision loaded successfully',
      type: 'success'
    });
    setTimeout(() => setNotification(null), 3000);
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
      const response = await apiClient.post('/vision/quality-check', {
        visionStatement,
        domain: selectedDomains[0]?.domain || 'general'
      });
      // Interceptor unwraps { success: true, data } to data directly
      setVisionQuality(response.data);
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

  const [optimizationJobId, setOptimizationJobId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [optimizationStatus, setOptimizationStatus] = useState<string>('');

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const checkOptimizationStatus = async (jobId: string) => {
    try {
      const response = await apiClient.get(`/vision/optimize/status/${jobId}`);
      const result = response.data;
      
      // Update status message
      if (result.status === 'processing') {
        setOptimizationStatus('Processing your vision statement...');
      } else if (result.status === 'pending') {
        setOptimizationStatus('Optimization queued, starting soon...');
      }
      
      if (result.status === 'completed') {
        // Stop polling
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        setIsPolling(false);
        setOptimizationJobId(null);
        setOptimizationStatus('');
        setIsOptimizing(false);
        
        // Transform to match expected format
        const optimizationResult = {
          vision_id: result.optimized_vision_id,
          optimized_vision: result.optimized_vision,
          original_score: result.original_assessment?.score || 0,
          optimized_score: result.quality_score,
          score_improvement: result.quality_score - (result.original_assessment?.score || 0),
          rating_change: `${result.original_assessment?.rating || 'N/A'} → ${result.quality_rating}`,
          improvements_made: result.optimization_feedback?.improvements_made || [],
          remaining_issues: result.optimization_feedback?.remaining_issues || [],
          is_acceptable: result.quality_score >= 75,
          original_assessment: result.original_assessment,
          optimized_assessment: result.optimization_feedback
        };
        
        setOptimizationResult(optimizationResult);
        setNotification({
          message: `Vision quality improved! Score: ${result.quality_score}`,
          type: 'success'
        });
        setTimeout(() => setNotification(null), 5000);
        
      } else if (result.status === 'failed') {
        // Stop polling on failure
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        setIsPolling(false);
        setOptimizationJobId(null);
        setOptimizationStatus('');
        setIsOptimizing(false);
        
        setNotification({
          message: result.error_message || 'Optimization failed',
          type: 'error'
        });
        setTimeout(() => setNotification(null), 8000);
      }
      // If status is 'pending' or 'processing', continue polling
      
    } catch (error: any) {
      console.error('Failed to check optimization status:', error);
      // Don't stop polling on transient errors
    }
  };

  const handleOptimize = async () => {
    const trimmedVision = visionStatement.trim();
    if (!trimmedVision) {
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
    setOptimizationResult(null); // Clear any previous results
    setOptimizationStatus('Starting optimization...');
    
    try {
      const requestData = {
        original_vision: trimmedVision,
        domains: selectedDomains
      };
      console.log('Starting async optimization:', requestData);
      
      // Use async endpoint
      const response = await apiClient.post('/vision/optimize/async', requestData);
      const result = response.data;
      
      if (result.job_id) {
        setOptimizationJobId(result.job_id);
        setIsPolling(true);
        
        setNotification({
          message: 'Vision optimization started. This may take up to 30 seconds...',
          type: 'success'
        });
        setTimeout(() => setNotification(null), 5000);
        
        // Start polling for status
        const interval = setInterval(() => {
          checkOptimizationStatus(result.job_id);
        }, 2000); // Check every 2 seconds
        
        setPollingInterval(interval);
        
        // Also check immediately
        checkOptimizationStatus(result.job_id);
      }
    } catch (error: any) {
      console.error('Optimization failed:', error);
      console.error('Error type:', error.name);
      console.error('Error response:', error.response);
      console.error('Error request:', error.request);
      console.error('Error config:', error.config);
      
      let errorMessage = 'Unable to optimize vision. Please try again.';
      
      if (error.name === 'NetworkError') {
        errorMessage = 'Network timeout: The optimization is taking longer than expected. The vision may still be processing and will appear in your history when complete. Please check your saved visions in a moment.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setNotification({
        message: errorMessage,
        type: 'error'
      });
      setTimeout(() => setNotification(null), 8000);
    } finally {
      if (!isPolling) {
        setIsOptimizing(false);
        setOptimizationStatus('');
      }
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

  const generateMarkdownReport = () => {
    if (!optimizationResult) return '';

    const timestamp = new Date().toISOString().split('T')[0];
    const domainNames = selectedDomains.map(d => {
      const domain = availableDomains.find(ad => ad.domain_key === d.domain);
      return domain ? domain.display_name : d.domain;
    }).join(', ');

    let markdown = `# Vision Optimization Report\n\n`;
    markdown += `**Date:** ${timestamp}\n`;
    markdown += `**Domains:** ${domainNames}\n\n`;

    // Quality Improvement Summary
    markdown += `## Quality Improvement Summary\n\n`;
    markdown += `- **Original Score:** ${optimizationResult.original_score}/100 (${optimizationResult.rating_change.split(' → ')[0]})\n`;
    markdown += `- **Optimized Score:** ${optimizationResult.optimized_score}/100 (${optimizationResult.rating_change.split(' → ')[1]})\n`;
    markdown += `- **Improvement:** +${optimizationResult.score_improvement} points\n\n`;

    // Original Vision Analysis
    if (optimizationResult.original_assessment) {
      markdown += `## Original Vision Analysis\n\n`;
      
      if (optimizationResult.original_assessment.strengths?.length > 0) {
        markdown += `### ✓ What Was Good About Your Vision\n\n`;
        optimizationResult.original_assessment.strengths.forEach(strength => {
          markdown += `- ${strength}\n`;
        });
        markdown += `\n`;
      }

      if (optimizationResult.original_assessment.weaknesses?.length > 0 || 
          optimizationResult.original_assessment.missing_elements?.length > 0) {
        markdown += `### ⚠ Areas for Improvement\n\n`;
        optimizationResult.original_assessment.weaknesses?.forEach(weakness => {
          markdown += `- ${weakness}\n`;
        });
        optimizationResult.original_assessment.missing_elements?.forEach(element => {
          markdown += `- Missing: ${element}\n`;
        });
        markdown += `\n`;
      }
    }

    // Key Enhancements Applied
    if (optimizationResult.improvements_made.length > 0) {
      markdown += `## 🔧 Key Enhancements Applied\n\n`;
      optimizationResult.improvements_made.forEach(improvement => {
        markdown += `- ${improvement}\n`;
      });
      markdown += `\n`;
    }

    // Original Vision Statement
    if (visionStatement) {
      markdown += `## Original Vision Statement\n\n`;
      markdown += `${visionStatement}\n\n`;
    }

    // Optimized Vision Statement
    markdown += `## Optimized Vision Statement\n\n`;
    markdown += `${optimizationResult.optimized_vision}\n\n`;

    // Tips for Future Vision Statements
    if (optimizationResult.original_assessment?.improvement_suggestions && optimizationResult.original_assessment.improvement_suggestions.length > 0) {
      markdown += `## 💡 Tips for Future Vision Statements\n\n`;
      optimizationResult.original_assessment.improvement_suggestions.forEach(tip => {
        markdown += `- ${tip}\n`;
      });
      markdown += `\n`;
    }

    // Remaining Issues
    if (optimizationResult.remaining_issues.length > 0) {
      markdown += `## Remaining Considerations\n\n`;
      optimizationResult.remaining_issues.forEach(issue => {
        markdown += `- ${issue}\n`;
      });
      markdown += `\n`;
    }

    return markdown;
  };

  const downloadMarkdownReport = () => {
    const markdown = generateMarkdownReport();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vision-optimization-report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setNotification({
      message: 'Markdown report downloaded successfully',
      type: 'success'
    });
    setTimeout(() => setNotification(null), 3000);
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
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Original Vision Statement</CardTitle>
                    <Dialog open={visionDialogOpen} onOpenChange={setVisionDialogOpen}>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => fetchSavedVisions()}
                        >
                          <History className="mr-2 h-4 w-4" />
                          Load Saved Vision
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden">
                        <DialogHeader>
                          <DialogTitle>Your Saved Visions</DialogTitle>
                          <DialogDescription>
                            Select a previously optimized vision to load it into the editor
                          </DialogDescription>
                        </DialogHeader>
                        <div className="overflow-y-auto max-h-[calc(80vh-120px)] pr-4">
                          {isLoadingVisions ? (
                            <div className="flex items-center justify-center py-8">
                              <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            </div>
                          ) : savedVisions.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                              <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
                              <p>No saved visions found</p>
                              <p className="text-sm mt-2">Optimized visions will appear here after you save them</p>
                            </div>
                          ) : (
                            <div className="space-y-4">
                              {savedVisions.map((vision) => (
                                <Card
                                  key={vision.id}
                                  className="p-4 hover:border-primary cursor-pointer transition-colors"
                                  onClick={() => handleLoadVision(vision)}
                                >
                                  <div className="space-y-2">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                          <Badge variant={vision.quality_score >= 80 ? "default" : "secondary"}>
                                            <Award className="mr-1 h-3 w-3" />
                                            {vision.quality_score}/100
                                          </Badge>
                                          <Badge variant="outline">{vision.quality_rating}</Badge>
                                          <span className="text-xs text-muted-foreground">
                                            <Calendar className="inline mr-1 h-3 w-3" />
                                            {new Date(vision.created_at).toLocaleDateString()}
                                          </span>
                                        </div>
                                        <p className="text-sm line-clamp-3 mb-2">
                                          {vision.optimized_vision}
                                        </p>
                                        {vision.domains && (
                                          <div className="flex gap-2 flex-wrap">
                                            {(typeof vision.domains === 'string' ? JSON.parse(vision.domains) : vision.domains).map((d: any, idx: number) => (
                                              <Badge key={idx} variant="outline" className="text-xs">
                                                {d.domain}
                                              </Badge>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </Card>
                              ))}
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
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
                            title={`${domain.display_name}: ${domain.description}`}
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
                  disabled={isOptimizing || isPolling || !visionStatement.trim() || selectedDomains.length === 0}
                >
                  {(isOptimizing || isPolling) ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      {optimizationStatus || 'Optimizing Vision...'}
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
                {isPolling && !optimizationResult ? (
                  <Card className="tron-card">
                    <CardHeader>
                      <CardTitle>Optimization In Progress</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-col items-center justify-center py-8">
                        <Loader2 className="h-16 w-16 animate-spin text-primary mb-4" />
                        <p className="text-lg font-medium">{optimizationStatus}</p>
                        <p className="text-sm text-muted-foreground mt-2">
                          This typically takes 20-30 seconds
                        </p>
                      </div>
                      <Progress value={100} className="h-2 animate-pulse" />
                    </CardContent>
                  </Card>
                ) : optimizationResult ? (
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

                      {/* Educational Summary Report */}
                      <div className="border rounded-lg p-4 space-y-4 bg-background/50">
                        <h4 className="font-semibold text-lg flex items-center gap-2">
                          <FiInfo className="h-5 w-5 text-primary" />
                          Vision Analysis Report
                        </h4>
                        
                        {/* What was good about the original */}
                        {optimizationResult.original_assessment?.strengths && optimizationResult.original_assessment.strengths.length > 0 && (
                          <div>
                            <h5 className="font-medium text-green-600 dark:text-green-400 mb-2">✓ What Was Good About Your Vision</h5>
                            <ul className="space-y-1">
                              {optimizationResult.original_assessment.strengths.map((strength: string, idx: number) => (
                                <li key={idx} className="text-sm text-muted-foreground pl-4">• {strength}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* What was missing or weak */}
                        {((optimizationResult.original_assessment?.weaknesses && optimizationResult.original_assessment.weaknesses.length > 0) ||
                          (optimizationResult.original_assessment?.missing_elements && optimizationResult.original_assessment.missing_elements.length > 0)) && (
                          <div>
                            <h5 className="font-medium text-orange-600 dark:text-orange-400 mb-2">⚠ Areas for Improvement</h5>
                            <ul className="space-y-1">
                              {optimizationResult.original_assessment?.weaknesses?.map((weakness: string, idx: number) => (
                                <li key={`w-${idx}`} className="text-sm text-muted-foreground pl-4">• {weakness}</li>
                              ))}
                              {optimizationResult.original_assessment?.missing_elements?.map((element: string, idx: number) => (
                                <li key={`m-${idx}`} className="text-sm text-muted-foreground pl-4">• Missing: {element}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Key improvements made */}
                        {optimizationResult.improvements_made.length > 0 && (
                          <div>
                            <h5 className="font-medium text-blue-600 dark:text-blue-400 mb-2">🔧 Key Enhancements Applied</h5>
                            <ul className="space-y-1">
                              {optimizationResult.improvements_made.map((improvement: string, idx: number) => (
                                <li key={idx} className="text-sm text-muted-foreground pl-4">• {improvement}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Learning tips */}
                        {optimizationResult.original_assessment?.improvement_suggestions && optimizationResult.original_assessment.improvement_suggestions.length > 0 && (
                          <div className="mt-3 p-3 rounded-md bg-primary/5 border border-primary/10">
                            <h5 className="font-medium text-primary mb-2">💡 Tips for Future Vision Statements</h5>
                            <ul className="space-y-1">
                              {optimizationResult.original_assessment.improvement_suggestions.map((tip: string, idx: number) => (
                                <li key={idx} className="text-sm text-muted-foreground">• {tip}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Optimized Vision */}
                      <div>
                        <h4 className="font-medium mb-2">Optimized Vision</h4>
                        <div className="bg-muted/50 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                          <p className="text-sm whitespace-pre-wrap">{optimizationResult.optimized_vision}</p>
                        </div>
                      </div>

                      {/* Quality Alert for scores below 75 */}
                      {!optimizationResult.is_acceptable && (
                        <Alert className="border-orange-500">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            <div className="space-y-1">
                              <p className="font-medium">Score: {optimizationResult.optimized_score}/100 - Below recommended threshold</p>
                              <p className="text-sm">The optimized vision scored below 75. You can:</p>
                              <ul className="text-sm ml-4 mt-1 space-y-0.5">
                                <li>• Retry optimization (AI will try a different approach)</li>
                                <li>• Edit the text and retry with your changes</li>
                                <li>• Use it anyway if you're satisfied with the content</li>
                              </ul>
                            </div>
                          </AlertDescription>
                        </Alert>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        {optimizationResult.is_acceptable ? (
                          <Button
                            className="flex-1"
                            onClick={handleApproveAndCreate}
                          >
                            Approve & Create New Backlog
                          </Button>
                        ) : (
                          <>
                            <Button
                              className="flex-1"
                              onClick={() => {
                                // Keep the optimized vision in the input and retry
                                setVisionStatement(optimizationResult.optimized_vision);
                                setOptimizationResult(null);
                                // Automatically trigger re-optimization after a short delay
                                setTimeout(() => {
                                  handleOptimize();
                                }, 100);
                              }}
                            >
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Retry Optimization
                            </Button>
                            <Button
                              variant="secondary"
                              onClick={handleApproveAndCreate}
                            >
                              Use Anyway
                            </Button>
                          </>
                        )}
                        <Button
                          variant="outline"
                          onClick={() => {
                            setVisionStatement(optimizationResult.optimized_vision);
                            setOptimizationResult(null);
                          }}
                        >
                          Edit & Retry
                        </Button>
                        <Button
                          variant="outline"
                          onClick={downloadMarkdownReport}
                          title="Download a formatted markdown report of the optimization results"
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Download Report
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