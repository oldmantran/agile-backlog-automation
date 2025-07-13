import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { 
  FiArrowLeft, 
  FiTrash2, 
  FiSearch,
  FiAlertTriangle,
  FiCheckCircle,
  FiLoader,
  FiFilter
} from 'react-icons/fi';

interface WorkItem {
  id: number;
  title: string;
  type: string;
  state: string;
  areaPath: string;
  assignedTo?: string;
}

const TronCleanupWorkItemsScreen: React.FC = () => {
  const navigate = useNavigate();
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteProgress, setDeleteProgress] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadWorkItems();
  }, []);

  const loadWorkItems = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('/api/workitems');
      if (response.ok) {
        const data = await response.json();
        setWorkItems(data);
        setMessage({ type: 'info', text: `Loaded ${data.length} work items` });
      } else {
        setMessage({ type: 'error', text: 'Failed to load work items' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error connecting to Azure DevOps' });
    } finally {
      setLoading(false);
    }
  };

  const deleteSelectedItems = async () => {
    if (selectedItems.length === 0) return;

    setDeleting(true);
    setDeleteProgress(0);
    
    try {
      const response = await fetch('/api/workitems/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itemIds: selectedItems })
      });

      if (response.ok) {
        // Simulate progress updates
        for (let i = 0; i <= 100; i += 10) {
          setDeleteProgress(i);
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        setMessage({ type: 'success', text: `Successfully deleted ${selectedItems.length} work items` });
        setSelectedItems([]);
        loadWorkItems(); // Refresh the list
      } else {
        setMessage({ type: 'error', text: 'Failed to delete work items' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error during deletion process' });
    } finally {
      setDeleting(false);
      setDeleteProgress(0);
    }
  };

  const toggleSelectAll = () => {
    if (selectedItems.length === filteredWorkItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredWorkItems.map(item => item.id));
    }
  };

  const toggleSelectItem = (itemId: number) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const filteredWorkItems = workItems.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || item.type.toLowerCase().includes(filterType.toLowerCase());
    return matchesSearch && matchesFilter;
  });

  const workItemTypes = Array.from(new Set(workItems.map(item => item.type)));

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
            <FiTrash2 className="w-12 h-12 text-destructive pulse-glow" />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            WORK ITEM <span className="text-destructive">CLEANUP</span>
          </h1>
          <p className="text-muted-foreground font-mono">
            DELETE SELECTED AZURE DEVOPS WORK ITEMS
          </p>
        </div>

        {/* Controls */}
        <div className="max-w-6xl mx-auto space-y-6">
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary flex items-center">
                <FiFilter className="w-5 h-5 mr-2" />
                Search and Filter
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <Label htmlFor="search" className="text-foreground">Search Work Items</Label>
                  <div className="relative">
                    <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="search"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Search by title or type..."
                      className="tron-input pl-10"
                    />
                  </div>
                </div>
                
                <div className="w-48">
                  <Label htmlFor="filter" className="text-foreground">Filter by Type</Label>
                  <select
                    id="filter"
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="w-full px-3 py-2 bg-input border border-primary/30 rounded-md text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="all">All Types</option>
                    {workItemTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={loadWorkItems}
                  disabled={loading}
                  className="tron-button"
                >
                  {loading ? <FiLoader className="w-4 h-4 mr-2 animate-spin" /> : <FiSearch className="w-4 h-4 mr-2" />}
                  {loading ? 'SCANNING...' : 'SCAN WORK ITEMS'}
                </Button>

                <Button
                  onClick={toggleSelectAll}
                  disabled={filteredWorkItems.length === 0}
                  variant="outline"
                  className="border-primary/50 text-primary hover:bg-primary/10"
                >
                  {selectedItems.length === filteredWorkItems.length ? 'DESELECT ALL' : 'SELECT ALL'}
                </Button>

                <Button
                  onClick={deleteSelectedItems}
                  disabled={selectedItems.length === 0 || deleting}
                  variant="destructive"
                  className="bg-destructive hover:bg-destructive/90"
                >
                  {deleting ? <FiLoader className="w-4 h-4 mr-2 animate-spin" /> : <FiTrash2 className="w-4 h-4 mr-2" />}
                  DELETE SELECTED ({selectedItems.length})
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

          {/* Work Items List */}
          <Card className="tron-card">
            <CardHeader>
              <CardTitle className="text-primary">
                Work Items ({filteredWorkItems.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredWorkItems.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  {loading ? 'Scanning for work items...' : 'No work items found'}
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredWorkItems.map(item => (
                    <div
                      key={item.id}
                      className={`flex items-center space-x-4 p-3 rounded-lg border transition-all duration-200 ${
                        selectedItems.includes(item.id)
                          ? 'border-primary bg-primary/10'
                          : 'border-primary/20 hover:border-primary/40'
                      }`}
                    >
                      <Checkbox
                        checked={selectedItems.includes(item.id)}
                        onCheckedChange={() => toggleSelectItem(item.id)}
                        className="border-primary"
                      />
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-primary">#{item.id}</span>
                          <span className="font-semibold text-foreground">{item.title}</span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>Type: {item.type}</span>
                          <span>State: {item.state}</span>
                          <span>Area: {item.areaPath}</span>
                          {item.assignedTo && <span>Assigned: {item.assignedTo}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Warning */}
          <Alert className="border-red-500/50 bg-red-500/10">
            <FiAlertTriangle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-red-400">
              <strong>WARNING:</strong> This action cannot be undone. Selected work items will be permanently deleted from Azure DevOps.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    </div>
  );
};

export default TronCleanupWorkItemsScreen;
