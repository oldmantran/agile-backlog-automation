import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import Header from '../components/navigation/Header';
import Sidebar from '../components/navigation/Sidebar';
import { 
  Settings, 
  Plus, 
  RefreshCw, 
  Trash2, 
  CheckSquare,
  Zap,
  Grid3X3,
  Cpu,
  Activity
} from 'lucide-react';
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

const TronWelcomeScreen: React.FC = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Combined menu items from both original Tron screen and dashboard
  const quickActions = [
    {
      title: 'Create New Backlog',
      description: 'Generate backlog from vision statement using AI',
      icon: Plus,
      route: '/new-project',
      color: 'primary',
      glowColor: 'primary',
      isNew: true,
      tronColor: 'blue'
    },
    {
      title: 'Configure Environment',
      description: 'Set up Azure DevOps credentials and AI providers',
      icon: Settings,
      route: '/configure',
      color: 'primary',
      glowColor: 'primary',
      isNew: false,
      tronColor: 'gray'
    },
    {
      title: 'Backlog Sweeper',
      description: 'Validate and enhance existing backlog items',
      icon: RefreshCw,
      route: '/sweeper',
      color: 'accent',
      glowColor: 'accent',
      isNew: false,
      tronColor: 'green'
    },
    {
      title: 'Cleanup Work Items',
      description: 'Clean up work items from specific area paths',
      icon: Trash2,
      route: '/cleanup-workitems',
      color: 'primary',
      glowColor: 'primary',
      isNew: false,
      tronColor: 'red'
    },
    {
      title: 'Delete Project Tests',
      description: 'Delete all test plans, suites, and test cases in area path',
      icon: CheckSquare,
      route: '/cleanup-tests',
      color: 'primary',
      glowColor: 'primary',
      isNew: false,
      tronColor: 'orange'
    },
    {
      title: 'Search Documentation',
      description: 'Find information in project documentation and repositories',
      icon: FiSearch,
      route: '/search',
      color: 'primary',
      glowColor: 'primary',
      isNew: false,
      tronColor: 'purple'
    }
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
      case 'blue': return 'hover:border-blue-400 hover:shadow-blue-500/20';
      case 'red': return 'hover:border-red-400 hover:shadow-red-500/20';
      case 'orange': return 'hover:border-orange-400 hover:shadow-orange-500/20';
      case 'green': return 'hover:border-green-400 hover:shadow-green-500/20';
      case 'purple': return 'hover:border-purple-400 hover:shadow-purple-500/20';
      case 'gray': return 'hover:border-gray-400 hover:shadow-gray-500/20';
      default: return 'hover:border-primary hover:shadow-primary/20';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-orange-400';
      case 'info': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header and Sidebar */}
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Main Content with Enhanced Tron styling */}
      <div className="ml-0 lg:ml-[250px] pt-[70px] transition-all duration-300 ease-in-out">
        <div className="min-h-screen bg-background tron-grid relative overflow-hidden">
          {/* Enhanced grid background overlay */}
          <div className="absolute inset-0 opacity-20">
            <div className="grid-pattern absolute inset-0"></div>
          </div>

          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-15">
            <div className="scan-line absolute w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent"></div>
          </div>

          {/* Enhanced matrix rain effect */}
          <div className="absolute inset-0 opacity-10 pointer-events-none">
            {[...Array(30)].map((_, i) => (
              <div
                key={i}
                className="absolute w-px h-20 bg-gradient-to-b from-primary to-transparent matrix-rain"
                style={{
                  left: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 20}s`,
                  animationDuration: `${15 + Math.random() * 10}s`
                }}
              />
            ))}
          </div>

          {/* Additional glow orbs - reduced opacity */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-primary/7 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute top-3/4 right-1/4 w-40 h-40 bg-accent/7 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
            <div className="absolute top-1/2 left-3/4 w-24 h-24 bg-primary/10 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }}></div>
          </div>

          <div className="relative z-10 container mx-auto px-6 py-8">
            {/* Header - positioned right next to sidebar */}
            <div className="text-center mb-12">
              <div className="flex items-center justify-center mb-6">
                <div className="relative">
                  <div className="absolute inset-0 w-20 h-20 bg-primary/20 rounded-lg blur-xl animate-pulse glow-cyan"></div>
                  <Grid3X3 className="w-16 h-16 text-primary pulse-glow relative z-10 glow-cyan" />
                  <div className="absolute inset-0 w-16 h-16 border-2 border-primary/50 rounded-lg rotate-45 animate-pulse glow-cyan"></div>
                  <div className="absolute inset-0 w-20 h-20 border border-accent/30 rounded-lg rotate-12 animate-pulse glow-cyan" style={{ animationDelay: '0.5s' }}></div>
                </div>
              </div>
              
              <h1 className="text-6xl font-bold text-foreground mb-4 tracking-wider glow-cyan">
                <span className="text-primary glow-cyan">AGILE</span>
                <span className="text-accent mx-2 glow-cyan">•</span>
                <span className="text-primary glow-cyan">DASHBOARD</span>
              </h1>
              
              <div className="text-2xl font-light text-muted-foreground tracking-widest mb-2 glow-cyan">
                BACKLOG AUTOMATION SYSTEM
              </div>
              
              <div className="text-sm text-primary font-mono glow-cyan">
                SYSTEM TIME: {currentTime.toLocaleTimeString()} | STATUS: <span className="text-accent glow-cyan">ONLINE</span>
              </div>
            </div>

            {/* Welcome Alert */}
            <Alert className="tron-card mb-8">
              <FiInfo className="w-4 h-4" />
              <AlertDescription>
                Welcome to the Agile Dashboard! Choose from the actions below to initialize 
                your project management protocols.
              </AlertDescription>
            </Alert>

            {/* System Status Bar */}
            <div className="tron-card mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-5 h-5 text-primary" />
                    <span className="text-sm font-mono text-foreground">CPU: <span className="text-green-400">ONLINE</span></span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Activity className="w-5 h-5 text-accent" />
                    <span className="text-sm font-mono text-foreground">AI: <span className="text-green-400">READY</span></span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-primary" />
                    <span className="text-sm font-mono text-foreground">DEVOPS: <span className="text-green-400">CONNECTED</span></span>
                  </div>
                </div>
                <div className="text-xs font-mono text-muted-foreground">
                  BUILD: <span className="text-primary">2025.07.14</span>
                </div>
              </div>
            </div>

            {/* Quick Actions Grid */}
            <div className="mb-12">
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">SYSTEM OPERATIONS</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                {quickActions.map((action, index) => {
                  const IconComponent = action.icon;
                  return (
                    <Card 
                      key={index}
                      className={`group bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-primary/60 hover:glow-cyan transition-all duration-300 cursor-pointer relative overflow-hidden tron-card ${getCardColorClass(action.tronColor)}`}
                      onClick={() => navigate(action.route)}
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="absolute inset-0 bg-gradient-to-tr from-accent/5 to-transparent opacity-0 group-hover:opacity-50 transition-opacity duration-300"></div>
                      
                      <CardHeader className="relative z-10 pb-3">
                        <div className="flex items-center justify-between mb-4">
                          <IconComponent className="w-8 h-8 text-primary group-hover:text-accent group-hover:glow-cyan transition-all duration-300" />
                          <div className="flex items-center space-x-2">
                            {action.isNew && (
                              <Badge variant="default" className="bg-green-500/20 text-green-400 border-green-400/50 glow-cyan">
                                NEW
                              </Badge>
                            )}
                            <div className="w-2 h-2 bg-primary rounded-full animate-pulse glow-cyan"></div>
                          </div>
                        </div>
                        <CardTitle className="text-xl font-semibold text-foreground group-hover:text-primary group-hover:glow-cyan transition-all duration-300">
                          {action.title}
                        </CardTitle>
                      </CardHeader>
                      
                      <CardContent className="relative z-10">
                        <p className="text-muted-foreground group-hover:text-foreground transition-colors duration-300 mb-4">
                          {action.description}
                        </p>
                        
                        <Button 
                          variant="outline" 
                          className="w-full tron-button border-primary/50 text-primary hover:bg-primary hover:text-primary-foreground"
                        >
                          INITIALIZE
                        </Button>
                      </CardContent>

                      {/* Hover effect lines */}
                      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-primary to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="mb-12">
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">RECENT ACTIVITY</h2>
              <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <FiActivity className="w-5 h-5 text-primary" />
                    <CardTitle className="text-foreground">System Activity Log</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-background/50 border border-primary/20">
                        <FiActivity className={`w-4 h-4 mt-1 ${getActivityIcon(activity.type)}`} />
                        <div className="flex-1 space-y-1">
                          <h4 className="font-medium text-foreground">{activity.title}</h4>
                          <p className="text-sm text-muted-foreground">{activity.description}</p>
                          <p className="text-xs text-primary font-mono">{activity.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* System Status */}
            <div className="mb-12">
              <h2 className="text-2xl font-semibold text-foreground mb-6 tracking-wider glow-cyan">SYSTEM STATUS</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-primary/50 transition-all duration-300">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-2">
                      <div className="w-3 h-3 bg-green-400 rounded-full mx-auto animate-pulse"></div>
                      <p className="font-medium text-foreground font-mono">AZURE DEVOPS API</p>
                      <p className="text-sm text-green-400 font-mono">CONNECTED</p>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-primary/50 transition-all duration-300">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-2">
                      <div className="w-3 h-3 bg-green-400 rounded-full mx-auto animate-pulse"></div>
                      <p className="font-medium text-foreground font-mono">AI SERVICES</p>
                      <p className="text-sm text-green-400 font-mono">OPERATIONAL</p>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="tron-card bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-accent/50 transition-all duration-300">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-2">
                      <div className="w-3 h-3 bg-yellow-400 rounded-full mx-auto animate-pulse"></div>
                      <p className="font-medium text-foreground font-mono">BACKGROUND JOBS</p>
                      <p className="text-sm text-yellow-400 font-mono">2 ACTIVE</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Footer */}
            <div className="text-center mt-12 text-xs font-mono text-muted-foreground">
              <div className="mb-2">TRON AUTOMATION INTERFACE v2.0</div>
              <div className="flex items-center justify-center space-x-4">
                <span>SECURE CONNECTION</span>
                <span>•</span>
                <span>ENCRYPTED DATA</span>
                <span>•</span>
                <span>AI ENHANCED</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TronWelcomeScreen;
