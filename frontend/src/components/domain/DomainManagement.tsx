import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { 
  FiPlus, 
  FiGlobe, 
  FiEdit3, 
  FiTrash2, 
  FiInfo, 
  FiCheck, 
  FiX,
  FiSave,
  FiLoader
} from 'react-icons/fi';

interface Domain {
  id: number;
  domain_key: string;
  display_name: string;
  description: string;
  is_active: boolean;
  is_system_default: boolean;
  pattern_count?: number;
  user_type_count?: number;
}

interface DomainRequest {
  domain_name: string;
  industry_description: string;
  use_case_description: string;
  target_users: string;
  key_terminology: string;
}

const DomainManagement: React.FC = () => {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{success?: boolean, message?: string} | null>(null);
  
  const [newDomainRequest, setNewDomainRequest] = useState<DomainRequest>({
    domain_name: '',
    industry_description: '',
    use_case_description: '',
    target_users: '',
    key_terminology: ''
  });

  // Load domains on component mount
  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/domains?include_patterns=true');
      if (response.ok) {
        const domainsData = await response.json();
        setDomains(domainsData);
      }
    } catch (error) {
      console.error('Failed to load domains:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateAiContext = async () => {
    if (!newDomainRequest.domain_name || !newDomainRequest.industry_description) {
      return;
    }

    setAiGenerating(true);
    try {
      const response = await fetch('/api/domains/generate-context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_name: newDomainRequest.domain_name,
          industry_description: newDomainRequest.industry_description
        })
      });

      if (response.ok) {
        const aiContext = await response.json();
        setNewDomainRequest(prev => ({
          ...prev,
          use_case_description: aiContext.use_case_description || prev.use_case_description,
          target_users: aiContext.target_users || prev.target_users,
          key_terminology: aiContext.key_terminology || prev.key_terminology
        }));
      }
    } catch (error) {
      console.error('AI context generation failed:', error);
    } finally {
      setAiGenerating(false);
    }
  };

  const submitDomainRequest = async () => {
    setIsSubmitting(true);
    setSubmitStatus(null);
    
    try {
      const response = await fetch('/api/domain-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newDomainRequest,
          requested_by: 'user', // This would come from auth context in real app
          request_date: new Date().toISOString()
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSubmitStatus({ 
          success: true, 
          message: `Domain request submitted successfully! Request ID: ${result.request_id}` 
        });
        
        // Reset form
        setNewDomainRequest({
          domain_name: '',
          industry_description: '',
          use_case_description: '',
          target_users: '',
          key_terminology: ''
        });
        
        // Close dialog after 2 seconds
        setTimeout(() => {
          setShowAddDialog(false);
          setSubmitStatus(null);
        }, 2000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setSubmitStatus({ 
          success: false, 
          message: errorData.detail || 'Failed to submit domain request' 
        });
      }
    } catch (error) {
      setSubmitStatus({ 
        success: false, 
        message: 'Network error while submitting request' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleDomainActive = async (domainId: number, isActive: boolean) => {
    try {
      const response = await fetch(`/api/domains/${domainId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !isActive })
      });

      if (response.ok) {
        await loadDomains(); // Refresh the list
      }
    } catch (error) {
      console.error('Failed to toggle domain status:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <FiLoader className="w-6 h-6 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading domains...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-foreground font-medium glow-cyan">Industry Domains</p>
          <p className="text-sm text-muted-foreground">
            Manage available industry domains for project classification and context enhancement
          </p>
        </div>
        
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan">
              <FiPlus className="w-4 h-4 mr-2" />
              Request New Domain
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <FiGlobe className="w-5 h-5" />
                <span>Request New Industry Domain</span>
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-6 mt-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="domain_name">Domain Name *</Label>
                  <Input
                    id="domain_name"
                    value={newDomainRequest.domain_name}
                    onChange={(e) => setNewDomainRequest(prev => ({ ...prev, domain_name: e.target.value }))}
                    placeholder="e.g., Legal Services, Space Technology, Gaming"
                  />
                </div>
                
                <div>
                  <Label htmlFor="industry_description">Industry Description *</Label>
                  <Textarea
                    id="industry_description"
                    value={newDomainRequest.industry_description}
                    onChange={(e) => setNewDomainRequest(prev => ({ ...prev, industry_description: e.target.value }))}
                    placeholder="Describe the industry, its key characteristics, and main activities..."
                    className="min-h-[100px]"
                  />
                </div>
                
                {/* AI Generation Button */}
                <div className="flex justify-center">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={generateAiContext}
                    disabled={!newDomainRequest.domain_name || !newDomainRequest.industry_description || aiGenerating}
                    className="border-accent text-accent hover:bg-accent hover:text-accent-foreground"
                  >
                    {aiGenerating ? (
                      <>
                        <FiLoader className="w-4 h-4 mr-2 animate-spin" />
                        Generating AI Context...
                      </>
                    ) : (
                      <>
                        <FiGlobe className="w-4 h-4 mr-2" />
                        Generate AI Context
                      </>
                    )}
                  </Button>
                </div>
              </div>
              
              {/* AI-Enhanced Fields */}
              <div className="space-y-4 p-4 rounded-lg border border-border bg-muted/50">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <FiInfo className="w-4 h-4" />
                  <span>The following fields can be auto-populated by AI or filled manually:</span>
                </div>
                
                <div>
                  <Label htmlFor="use_case_description">Use Case & Applications</Label>
                  <Textarea
                    id="use_case_description"
                    value={newDomainRequest.use_case_description}
                    onChange={(e) => setNewDomainRequest(prev => ({ ...prev, use_case_description: e.target.value }))}
                    placeholder="Common use cases, applications, and project types in this domain..."
                    className="min-h-[80px]"
                  />
                </div>
                
                <div>
                  <Label htmlFor="target_users">Target User Types</Label>
                  <Input
                    id="target_users"
                    value={newDomainRequest.target_users}
                    onChange={(e) => setNewDomainRequest(prev => ({ ...prev, target_users: e.target.value }))}
                    placeholder="e.g., lawyers, judges, legal assistants, clients, compliance officers"
                  />
                </div>
                
                <div>
                  <Label htmlFor="key_terminology">Key Terminology & Vocabulary</Label>
                  <Textarea
                    id="key_terminology"
                    value={newDomainRequest.key_terminology}
                    onChange={(e) => setNewDomainRequest(prev => ({ ...prev, key_terminology: e.target.value }))}
                    placeholder="Industry-specific terms, processes, and vocabulary..."
                    className="min-h-[80px]"
                  />
                </div>
              </div>
              
              {/* Status Messages */}
              {submitStatus && (
                <Alert className={submitStatus.success ? 'border-green-500/50 bg-green-500/10' : 'border-red-500/50 bg-red-500/10'}>
                  {submitStatus.success ? <FiCheck className="w-4 h-4 text-green-500" /> : <FiX className="w-4 h-4 text-red-500" />}
                  <AlertDescription className={submitStatus.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}>
                    {submitStatus.message}
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <Button
                  onClick={submitDomainRequest}
                  disabled={!newDomainRequest.domain_name || !newDomainRequest.industry_description || isSubmitting}
                  className="flex-1 bg-primary hover:bg-primary/80 text-primary-foreground"
                >
                  {isSubmitting ? (
                    <>
                      <FiLoader className="w-4 h-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <FiSave className="w-4 h-4 mr-2" />
                      Submit Request
                    </>
                  )}
                </Button>
                
                <Button
                  variant="outline"
                  onClick={() => setShowAddDialog(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </div>
              
              <div className="p-3 rounded-lg border border-blue-500/30 bg-blue-500/10">
                <div className="flex items-center space-x-2 text-blue-300 text-sm">
                  <FiInfo className="w-4 h-4" />
                  <span>Domain requests are reviewed and processed by administrators. You'll be notified when your domain is approved and available.</span>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      
      {/* Domains Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 rounded-lg border border-primary/30 bg-card/20">
          <div className="text-2xl font-bold text-primary glow-cyan">{domains.length}</div>
          <div className="text-xs text-muted-foreground">Total Domains</div>
        </div>
        <div className="text-center p-3 rounded-lg border border-primary/30 bg-card/20">
          <div className="text-2xl font-bold text-green-400 glow-cyan">{domains.filter(d => d.is_active).length}</div>
          <div className="text-xs text-muted-foreground">Active</div>
        </div>
        <div className="text-center p-3 rounded-lg border border-primary/30 bg-card/20">
          <div className="text-2xl font-bold text-yellow-400 glow-cyan">{domains.filter(d => d.is_system_default).length}</div>
          <div className="text-xs text-muted-foreground">System Default</div>
        </div>
        <div className="text-center p-3 rounded-lg border border-primary/30 bg-card/20">
          <div className="text-2xl font-bold text-blue-400 glow-cyan">{domains.filter(d => !d.is_system_default).length}</div>
          <div className="text-xs text-muted-foreground">Custom</div>
        </div>
      </div>
      
      {/* Domains List */}
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {domains.map(domain => (
          <div 
            key={domain.id} 
            className="flex items-center justify-between p-3 rounded-lg border border-border bg-card/50 hover:bg-card/70 transition-colors"
          >
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <span className="font-medium text-foreground glow-cyan">{domain.display_name}</span>
                <div className="flex space-x-1">
                  {domain.is_system_default && (
                    <Badge variant="outline" className="text-xs px-2 py-0 border-yellow-500/50 text-yellow-400">
                      SYSTEM
                    </Badge>
                  )}
                  <Badge 
                    variant={domain.is_active ? "default" : "secondary"} 
                    className="text-xs px-2 py-0"
                  >
                    {domain.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {domain.description}
              </p>
              {(domain.pattern_count || domain.user_type_count) && (
                <div className="flex space-x-4 text-xs text-muted-foreground mt-2">
                  {domain.pattern_count && <span>{domain.pattern_count} patterns</span>}
                  {domain.user_type_count && <span>{domain.user_type_count} user types</span>}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2 ml-4">
              {!domain.is_system_default && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleDomainActive(domain.id, domain.is_active)}
                  className="h-8 w-8 p-0"
                >
                  {domain.is_active ? 
                    <FiX className="w-4 h-4 text-red-400" /> : 
                    <FiCheck className="w-4 h-4 text-green-400" />
                  }
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {domains.length === 0 && (
        <div className="text-center py-8">
          <FiGlobe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No domains found. Add your first domain to get started.</p>
        </div>
      )}
    </div>
  );
};

export default DomainManagement;