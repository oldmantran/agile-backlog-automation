import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  Badge,
  useToast,
  SimpleGrid,
  Icon,
  Divider,
  Link,
  Code,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tooltip,
  Spinner,
  useColorModeValue,
} from '@chakra-ui/react';
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
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  
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
      toast({
        title: 'Search Required',
        description: 'Please enter a search term',
        status: 'warning',
        duration: 3000,
      });
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
      toast({
        title: 'No Results',
        description: `No documents found matching "${searchQuery}"`,
        status: 'info',
        duration: 3000,
      });
    } else {
      toast({
        title: 'Search Complete',
        description: `Found ${searchResults.length} document(s) matching "${searchQuery}"`,
        status: 'success',
        duration: 3000,
      });
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
    toast({
      title: 'Opening Document',
      description: `Would open ${path} in editor`,
      status: 'info',
      duration: 2000,
    });
  };

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack>
          <Button
            leftIcon={<Icon as={FiArrowLeft} />}
            variant="ghost"
            onClick={() => navigate('/dashboard')}
          >
            Back to Dashboard
          </Button>
        </HStack>

        <Box>
          <Heading size="lg" mb={2} color="blue.500">
            <Icon as={FiBookOpen} mr={3} />
            Search Documentation
          </Heading>
          <Text color="gray.600">
            Search through all project documentation and guides
          </Text>
        </Box>

        {/* Search Section */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Document Search</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Search Query</FormLabel>
                <InputGroup size="lg">
                  <InputLeftElement>
                    <Icon as={FiSearch} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search documentation (e.g., 'agent', 'backlog', 'integration', 'API')"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <InputRightElement width="4.5rem">
                    {isSearching && <Spinner size="sm" />}
                  </InputRightElement>
                </InputGroup>
              </FormControl>

              <HStack>
                <Button
                  leftIcon={<Icon as={FiSearch} />}
                  colorScheme="blue"
                  onClick={handleSearch}
                  isLoading={isSearching}
                  loadingText="Searching..."
                >
                  Search
                </Button>
                <Button
                  leftIcon={<Icon as={FiRefreshCw} />}
                  variant="outline"
                  onClick={handleClearSearch}
                >
                  Clear
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Statistics and Filters */}
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="sm">Documentation Stats</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={3} align="stretch">
                <HStack justify="space-between">
                  <Text fontSize="sm">Total Documents:</Text>
                  <Badge colorScheme="blue">{stats.totalDocuments}</Badge>
                </HStack>
                <HStack justify="space-between">
                  <Text fontSize="sm">Last Indexed:</Text>
                  <Text fontSize="sm" color="gray.600">{stats.lastIndexed}</Text>
                </HStack>
                <HStack justify="space-between">
                  <Text fontSize="sm">Search Results:</Text>
                  <Badge colorScheme="green">{filteredResults.length}</Badge>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="sm">
                <Icon as={FiFilter} mr={2} />
                Filter by Category
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={2} align="stretch">
                <Button
                  size="sm"
                  variant={selectedCategory === 'all' ? 'solid' : 'ghost'}
                  colorScheme="blue"
                  onClick={() => setSelectedCategory('all')}
                  justifyContent="space-between"
                >
                  <Text>All Categories</Text>
                  <Badge>{stats.totalDocuments}</Badge>
                </Button>
                {Object.entries(stats.categories).map(([category, count]) => (
                  <Button
                    key={category}
                    size="sm"
                    variant={selectedCategory === category ? 'solid' : 'ghost'}
                    colorScheme="gray"
                    onClick={() => setSelectedCategory(category)}
                    justifyContent="space-between"
                  >
                    <Text>{category}</Text>
                    <Badge>{count}</Badge>
                  </Button>
                ))}
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Quick Search Suggestions */}
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Popular Searches:</AlertTitle>
            <AlertDescription>
              <HStack spacing={2} mt={2} wrap="wrap">
                {['agent', 'backlog sweeper', 'integration', 'QA', 'implementation', 'planning'].map((term) => (
                  <Button
                    key={term}
                    size="xs"
                    variant="outline"
                    onClick={() => {
                      setSearchQuery(term);
                      handleSearch();
                    }}
                  >
                    {term}
                  </Button>
                ))}
              </HStack>
            </AlertDescription>
          </Box>
        </Alert>

        {/* Search Results */}
        <Card bg={cardBg}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">
                Documentation Results
                {filteredResults.length > 0 && (
                  <Badge ml={2} colorScheme="blue">
                    {filteredResults.length} found
                  </Badge>
                )}
              </Heading>
              {searchQuery && (
                <Text fontSize="sm" color="gray.600">
                  Results for: <Code>"{searchQuery}"</Code>
                </Text>
              )}
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {filteredResults.length === 0 ? (
                <Box textAlign="center" py={8}>
                  <Icon as={FiFileText} size="48px" color="gray.400" mb={4} />
                  <Text color="gray.600" mb={2}>
                    {searchQuery ? 'No documents found matching your search' : 'Enter a search term to find documentation'}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    Try searching for terms like "agent", "backlog", or "implementation"
                  </Text>
                </Box>
              ) : (
                filteredResults.map((doc, index) => (
                  <Card key={index} variant="outline" _hover={{ bg: 'gray.50' }}>
                    <CardBody>
                      <VStack spacing={3} align="stretch">
                        <HStack justify="space-between">
                          <VStack align="start" spacing={1}>
                            <HStack>
                              <Heading size="sm" color="blue.600">
                                {doc.title}
                              </Heading>
                              {doc.matchCount > 0 && (
                                <Tooltip label={`Relevance Score: ${doc.relevanceScore}`}>
                                  <Badge colorScheme="green">
                                    {doc.matchCount} match{doc.matchCount !== 1 ? 'es' : ''}
                                  </Badge>
                                </Tooltip>
                              )}
                            </HStack>
                            <Code fontSize="xs" colorScheme="gray">
                              {doc.fileName}
                            </Code>
                          </VStack>
                          <VStack align="end" spacing={1}>
                            <Badge colorScheme="purple">{doc.category}</Badge>
                            <HStack spacing={2}>
                              <Icon as={FiClock} size="12px" color="gray.400" />
                              <Text fontSize="xs" color="gray.500">
                                {doc.lastModified}
                              </Text>
                            </HStack>
                          </VStack>
                        </HStack>
                        
                        <Text fontSize="sm" color="gray.600" noOfLines={2}>
                          {doc.excerpt}
                        </Text>
                        
                        <Divider />
                        
                        <HStack justify="space-between">
                          <HStack spacing={4}>
                            <HStack>
                              <Icon as={FiTag} size="12px" color="gray.400" />
                              <Text fontSize="xs" color="gray.500">
                                {doc.size}
                              </Text>
                            </HStack>
                          </HStack>
                          <Button
                            size="sm"
                            leftIcon={<Icon as={FiExternalLink} />}
                            onClick={() => openDocument(doc.path)}
                            colorScheme="blue"
                            variant="outline"
                          >
                            Open
                          </Button>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))
              )}
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
};

export default SearchDocumentationScreen;
