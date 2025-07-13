import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import {
  FiPlus,
  FiTrash2,
  FiRefreshCw,
  FiSearch,
  FiSettings,
  FiActivity,
  FiClipboard,
  FiInfo,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();

  const quickActions = [
    {
      title: 'Start New Project',
      description: 'Initialize a new agile project with automated backlog setup',
      icon: FiPlus,
      color: 'blue',
      path: '/project/create',
      isNew: true,
    },
    {
      title: 'Delete Work Items',
      description: 'Clean up work items from specific area paths',
      icon: FiTrash2,
      color: 'red',
      path: '/cleanup/workitems',
      isNew: false,
    },
    {
      title: 'Delete Test Cases',
      description: 'Clean up test cases using Test Management API',
      icon: FiClipboard,
      color: 'orange',
      path: '/cleanup/testcases',
      isNew: false,
    },
    {
      title: 'Backlog Sweeper',
      description: 'Enhance existing backlogs with AI-generated improvements',
      icon: FiRefreshCw,
      color: 'green',
      path: '/sweeper',
      isNew: false,
    },
    {
      title: 'Search Documentation',
      description: 'Find information in project documentation and repositories',
      icon: FiSearch,
      color: 'purple',
      path: '/search',
      isNew: false,
    },
    {
      title: 'System Settings',
      description: 'Configure Azure DevOps connections and preferences',
      icon: FiSettings,
      color: 'gray',
      path: '/settings',
      isNew: false,
    },
  ];

  const recentActivity = [
    {
      title: 'Project Alpha backlog generated',
      description: 'Successfully created 24 user stories and 8 epics',
      timestamp: '2 hours ago',
      type: 'success',
    },
    {
      title: 'Work items cleanup completed',
      description: 'Removed 156 orphaned work items from Data Visualization area',
      timestamp: '1 day ago',
      type: 'info',
    },
    {
      title: 'Test cases cleanup completed',
      description: 'Deleted 89 test cases using Test Management API',
      timestamp: '2 days ago',
      type: 'warning',
    },
  ];

  const getCardColorClass = (color: string) => {
    switch (color) {
      case 'blue': return 'hover:border-blue-300 hover:shadow-blue-100';
      case 'red': return 'hover:border-red-300 hover:shadow-red-100';
      case 'orange': return 'hover:border-orange-300 hover:shadow-orange-100';
      case 'green': return 'hover:border-green-300 hover:shadow-green-100';
      case 'purple': return 'hover:border-purple-300 hover:shadow-purple-100';
      case 'gray': return 'hover:border-gray-300 hover:shadow-gray-100';
      default: return 'hover:border-gray-300 hover:shadow-gray-100';
    }
  };

  const getIconColorClass = (color: string) => {
    switch (color) {
      case 'blue': return 'text-blue-600';
      case 'red': return 'text-red-600';
      case 'orange': return 'text-orange-600';
      case 'green': return 'text-green-600';
      case 'purple': return 'text-purple-600';
      case 'gray': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-orange-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-foreground">Agile Backlog Automation</h1>
          <p className="text-xl text-muted-foreground">
            Streamline your project management with AI-powered backlog generation and cleanup tools
          </p>
        </div>

        {/* Welcome Alert */}
        <Alert>
          <FiInfo className="w-4 h-4" />
          <AlertDescription>
            Welcome to the Agile Backlog Automation platform! Choose from the actions below to get started 
            with your project management workflow.
          </AlertDescription>
        </Alert>

        {/* Quick Actions Grid */}
        <div>
          <h2 className="text-2xl font-semibold text-foreground mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quickActions.map((action, index) => {
              const IconComponent = action.icon;
              return (
                <Card 
                  key={index} 
                  className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${getCardColorClass(action.color)}`}
                  onClick={() => navigate(action.path)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <IconComponent className={`w-8 h-8 ${getIconColorClass(action.color)}`} />
                      {action.isNew && (
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          NEW
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <CardTitle className="text-lg">{action.title}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {action.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-2xl font-semibold text-foreground mb-6">Recent Activity</h2>
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <FiActivity className="w-5 h-5 text-muted-foreground" />
                <CardTitle>System Activity</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-muted/50">
                    <FiActivity className={`w-4 h-4 mt-1 ${getActivityIcon(activity.type)}`} />
                    <div className="flex-1 space-y-1">
                      <h4 className="font-medium text-foreground">{activity.title}</h4>
                      <p className="text-sm text-muted-foreground">{activity.description}</p>
                      <p className="text-xs text-muted-foreground">{activity.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Status */}
        <div>
          <h2 className="text-2xl font-semibold text-foreground mb-6">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center space-y-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full mx-auto"></div>
                  <p className="font-medium text-foreground">Azure DevOps API</p>
                  <p className="text-sm text-muted-foreground">Connected</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="text-center space-y-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full mx-auto"></div>
                  <p className="font-medium text-foreground">AI Services</p>
                  <p className="text-sm text-muted-foreground">Operational</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="text-center space-y-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mx-auto"></div>
                  <p className="font-medium text-foreground">Background Jobs</p>
                  <p className="text-sm text-muted-foreground">2 Active</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer Info */}
        <div className="text-center text-sm text-muted-foreground py-8">
          <p>
            Agile Backlog Automation Platform • Built with AI-powered project management tools
          </p>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
