import React, { useState, useEffect } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Separator } from '../../components/ui/separator';
import { 
  FiSearch, 
  FiArrowLeft, 
  FiFileText, 
  FiClock, 
  FiTag,
  FiExternalLink,
  FiFilter,
  FiRefreshCw,
  FiTrendingUp,
  FiBookOpen
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface DocumentResult {
  fileName: string;
  title: string;
  path: string;
  category: string;
  lastModified: string;
  size: string;
  excerpt: string;
  matchCount: number;
  relevanceScore: number;
}

interface SearchStats {
  totalDocuments: number;
  categories: { [key: string]: number };
  lastIndexed: string;
}

const SearchDocumentationScreen: React.FC = () => {
  const navigate = useNavigate();
  // Toast functionality can be added with react-hot-toast or shadcn/ui toast
  // const toast = useToast();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<DocumentResult[]>([]);
  const [stats, setStats] = useState<SearchStats>({
    totalDocuments: 24,
    categories: {
      'Implementation': 8,
      'Planning': 6,
      'Agent Documentation': 5,
      'API Reference': 3,
      'User Guides': 2,
    },
    lastIndexed: new Date().toLocaleDateString(),
  });
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock documentation data based on the actual docs folder
  const mockDocuments: DocumentResult[] = [
    {
      fileName: 'AUTONOMOUS_BACKLOG_ENHANCEMENT_PLAN.md',
      title: 'Autonomous Backlog Enhancement Plan',
      path: '/docs/AUTONOMOUS_BACKLOG_ENHANCEMENT_PLAN.md',
      category: 'Planning',
      lastModified: '2024-01-15',
      size: '15.2 KB',
      excerpt: 'Comprehensive plan for automated backlog enhancement using AI agents and quality compliance checks...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'COMPREHENSIVE_AGENT_SUMMARY.md',
      title: 'Comprehensive Agent Summary',
      path: '/docs/COMPREHENSIVE_AGENT_SUMMARY.md',
      category: 'Agent Documentation',
      lastModified: '2024-01-14',
      size: '22.8 KB',
      excerpt: 'Complete documentation of all AI agents including Epic Strategist, User Story Decomposer, and QA Lead Agent...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'BACKLOG_SWEEPER_DUAL_MODE_COMPLETE.md',
      title: 'Backlog Sweeper Dual Mode Implementation',
      path: '/docs/BACKLOG_SWEEPER_DUAL_MODE_COMPLETE.md',
      category: 'Implementation',
      lastModified: '2024-01-13',
      size: '18.5 KB',
      excerpt: 'Documentation for the dual-mode backlog sweeper with manual and automatic operation modes...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'QA_TESTER_AGENT_QUALITY_REPORT.md',
      title: 'QA Tester Agent Quality Report',
      path: '/docs/QA_TESTER_AGENT_QUALITY_REPORT.md',
      category: 'Agent Documentation',
      lastModified: '2024-01-12',
      size: '12.3 KB',
      excerpt: 'Quality assurance documentation and testing protocols for the automated QA agent system...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'FRONTEND_BACKEND_INTEGRATION.md',
      title: 'Frontend Backend Integration Guide',
      path: '/docs/FRONTEND_BACKEND_INTEGRATION.md',
      category: 'Implementation',
      lastModified: '2024-01-11',
      size: '9.7 KB',
      excerpt: 'Integration documentation for connecting the React frontend with the FastAPI backend...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'SIMPLIFIED_UI_README.md',
      title: 'Simplified UI README',
      path: '/docs/SIMPLIFIED_UI_README.md',
      category: 'User Guides',
      lastModified: '2024-01-10',
      size: '6.4 KB',
      excerpt: 'User guide for the simplified UI interface with step-by-step instructions for common operations...',
      matchCount: 0,
      relevanceScore: 0,
    },
    {
      fileName: 'PROMPT_SYSTEM_GUIDE.md',
      title: 'Prompt System Guide',
      path: '/docs/PROMPT_SYSTEM_GUIDE.md',
      category: 'API Reference',
      lastModified: '2024-01-09',
      size: '14.1 KB',
      excerpt: 'Technical guide for the prompt system used by AI agents for automated backlog enhancement...',
      matchCount: 0,
      relevanceScore: 0,
    },
  ];

  useEffect(() => {
    // Simulate indexing on component mount
    setResults(mockDocuments);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // TODO: Add proper toast notification
      console.warn('Search Required: Please enter a search term');
      return;
    }

    setIsSearching(true);

    // Simulate search with scoring
    await new Promise(resolve => setTimeout(resolve, 800));

    const searchResults = mockDocuments
      .map(doc => {
        const query = searchQuery.toLowerCase();
        let matchCount = 0;
        let relevanceScore = 0;

        // Check title matches (higher weight)
        if (doc.title.toLowerCase().includes(query)) {
          matchCount += 3;
          relevanceScore += 30;
        }

        // Check excerpt matches
        if (doc.excerpt.toLowerCase().includes(query)) {
          matchCount += 2;
          relevanceScore += 20;
        }

        // Check category matches
        if (doc.category.toLowerCase().includes(query)) {
          matchCount += 1;
          relevanceScore += 10;
        }

        // Check filename matches
        if (doc.fileName.toLowerCase().includes(query)) {
          matchCount += 2;
          relevanceScore += 15;
        }

        return { ...doc, matchCount, relevanceScore };
      })
      .filter(doc => doc.matchCount > 0)
      .sort((a, b) => b.relevanceScore - a.relevanceScore);

    setResults(searchResults);
    setIsSearching(false);

    if (searchResults.length === 0) {
      // TODO: Add proper toast notification
      console.info(`No Results: No documents found matching "${searchQuery}"`);
    } else {
      // TODO: Add proper toast notification
      console.info(`Search Complete: Found ${searchResults.length} document(s) matching "${searchQuery}"`);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setResults(mockDocuments);
    setSelectedCategory('all');
  };

  const filteredResults = selectedCategory === 'all' 
    ? results 
    : results.filter(doc => doc.category === selectedCategory);

  const openDocument = (path: string) => {
    // TODO: Add proper toast notification
    console.info(`Opening Document: Would open ${path} in editor`);
  };

  return (
    <div className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="flex items-center"
          >
            <FiArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-primary mb-2 flex items-center">
            <FiBookOpen className="mr-3 h-6 w-6" />
            Search Documentation
          </h1>
          <p className="text-muted-foreground">
            Search through all project documentation and guides
          </p>
        </div>

        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle>Document Search</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="search-query">Search Query</Label>
                <div className="relative">
                  <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search-query"
                    placeholder="Search documentation (e.g., 'agent', 'backlog', 'integration', 'API')"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="pl-10 text-lg h-12"
                  />
                  {isSearching && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <Button
                  onClick={handleSearch}
                  disabled={isSearching}
                  className="flex items-center"
                >
                  <FiSearch className="mr-2 h-4 w-4" />
                  {isSearching ? 'Searching...' : 'Search'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClearSearch}
                  className="flex items-center"
                >
                  <FiRefreshCw className="mr-2 h-4 w-4" />
                  Clear
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Statistics and Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documentation Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Total Documents:</span>
                  <Badge variant="secondary">{stats.totalDocuments}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Last Indexed:</span>
                  <span className="text-sm text-muted-foreground">{stats.lastIndexed}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Search Results:</span>
                  <Badge>{filteredResults.length}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center">
                <FiFilter className="mr-2 h-4 w-4" />
                Filter by Category
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button
                  size="sm"
                  variant={selectedCategory === 'all' ? 'default' : 'ghost'}
                  onClick={() => setSelectedCategory('all')}
                  className="w-full justify-between"
                >
                  <span>All Categories</span>
                  <Badge variant="outline">{stats.totalDocuments}</Badge>
                </Button>
                {Object.entries(stats.categories).map(([category, count]) => (
                  <Button
                    key={category}
                    size="sm"
                    variant={selectedCategory === category ? 'default' : 'ghost'}
                    onClick={() => setSelectedCategory(category)}
                    className="w-full justify-between"
                  >
                    <span>{category}</span>
                    <Badge variant="outline">{count}</Badge>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Search Suggestions */}
        <Alert className="rounded-md">
          <div>
            <h4 className="font-medium mb-2">Popular Searches:</h4>
            <AlertDescription>
              <div className="flex flex-wrap gap-2 mt-2">
                {['agent', 'backlog sweeper', 'integration', 'QA', 'implementation', 'planning'].map((term) => (
                  <Button
                    key={term}
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSearchQuery(term);
                      handleSearch();
                    }}
                  >
                    {term}
                  </Button>
                ))}
              </div>
            </AlertDescription>
          </div>
        </Alert>

        {/* Search Results */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <CardTitle>Documentation Results</CardTitle>
                {filteredResults.length > 0 && (
                  <Badge className="ml-2">
                    {filteredResults.length} found
                  </Badge>
                )}
              </div>
              {searchQuery && (
                <span className="text-sm text-muted-foreground">
                  Results for: <code className="bg-muted px-1 py-0.5 rounded text-xs">"{searchQuery}"</code>
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredResults.length === 0 ? (
                <div className="text-center py-8">
                  <FiFileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-2">
                    {searchQuery ? 'No documents found matching your search' : 'Enter a search term to find documentation'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Try searching for terms like "agent", "backlog", or "implementation"
                  </p>
                </div>
              ) : (
                filteredResults.map((doc, index) => (
                  <Card key={index} className="border hover:bg-muted/50">
                    <CardContent className="pt-6">
                      <div className="space-y-3">
                        <div className="flex justify-between items-start">
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <h3 className="text-sm font-medium text-primary">
                                {doc.title}
                              </h3>
                              {doc.matchCount > 0 && (
                                <Badge variant="secondary" title={`Relevance Score: ${doc.relevanceScore}`}>
                                  {doc.matchCount} match{doc.matchCount !== 1 ? 'es' : ''}
                                </Badge>
                              )}
                            </div>
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              {doc.fileName}
                            </code>
                          </div>
                          <div className="text-right space-y-1">
                            <Badge variant="outline">{doc.category}</Badge>
                            <div className="flex items-center space-x-1">
                              <FiClock className="h-3 w-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">
                                {doc.lastModified}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {doc.excerpt}
                        </p>
                        
                        <Separator />
                        
                        <div className="flex justify-between items-center">
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-1">
                              <FiTag className="h-3 w-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">
                                {doc.size}
                              </span>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => openDocument(doc.path)}
                            variant="outline"
                            className="flex items-center"
                          >
                            <FiExternalLink className="mr-2 h-3 w-3" />
                            Open
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SearchDocumentationScreen;
