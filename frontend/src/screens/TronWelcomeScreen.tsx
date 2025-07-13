import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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

const TronWelcomeScreen: React.FC = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const menuItems = [
    {
      title: "Configure Environment",
      description: "Set up Azure DevOps credentials and AI providers",
      icon: Settings,
      route: "/configure",
      color: "primary",
      glowColor: "primary"
    },
    {
      title: "Create New Backlog",
      description: "Generate backlog from vision statement using AI",
      icon: Plus,
      route: "/new-project",
      color: "primary",
      glowColor: "primary"
    },
    {
      title: "Backlog Sweeper",
      description: "Validate and enhance existing backlog items",
      icon: RefreshCw,
      route: "/sweeper",
      color: "accent",
      glowColor: "accent"
    },
    {
      title: "Cleanup Work Items",
      description: "Delete selected Azure DevOps work items",
      icon: Trash2,
      route: "/cleanup-workitems",
      color: "primary",
      glowColor: "primary"
    },
    {
      title: "Cleanup Test Cases",
      description: "Remove test cases, suites, and plans",
      icon: CheckSquare,
      route: "/cleanup-tests",
      color: "primary",
      glowColor: "primary"
    }
  ];

  return (
    <div className="min-h-screen bg-background tron-grid relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 opacity-20">
        <div className="scan-line absolute w-full h-px bg-gradient-to-r from-transparent via-primary to-transparent"></div>
      </div>

      {/* Matrix rain effect */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        {[...Array(20)].map((_, i) => (
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

      <div className="relative z-10 container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <Grid3X3 className="w-16 h-16 text-primary pulse-glow" />
              <div className="absolute inset-0 w-16 h-16 border-2 border-primary/30 rounded-lg rotate-45 animate-pulse"></div>
            </div>
          </div>
          
          <h1 className="text-6xl font-bold text-foreground mb-4 tracking-wider">
            <span className="text-primary">AGILE</span>
            <span className="text-accent mx-2">•</span>
            <span className="text-primary">BACKLOG</span>
          </h1>
          
          <div className="text-2xl font-light text-muted-foreground tracking-widest mb-2">
            AUTOMATION SYSTEM
          </div>
          
          <div className="text-sm text-primary font-mono">
            SYSTEM TIME: {currentTime.toLocaleTimeString()} | STATUS: ONLINE
          </div>
        </div>

        {/* System Status Bar */}
        <div className="tron-card mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-primary" />
                <span className="text-sm font-mono text-foreground">CPU: ONLINE</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-accent" />
                <span className="text-sm font-mono text-foreground">AI: READY</span>
              </div>
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-primary" />
                <span className="text-sm font-mono text-foreground">DEVOPS: CONNECTED</span>
              </div>
            </div>
            <div className="text-xs font-mono text-muted-foreground">
              BUILD: 2025.07.13
            </div>
          </div>
        </div>

        {/* Main Menu Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {menuItems.map((item, index) => (
            <Card 
              key={index}
              className="group bg-card/50 backdrop-blur-sm border border-primary/30 hover:border-primary/60 transition-all duration-300 cursor-pointer relative overflow-hidden"
              onClick={() => navigate(item.route)}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              <CardHeader className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <item.icon className="w-8 h-8 text-primary group-hover:text-accent transition-colors duration-300" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                </div>
                <CardTitle className="text-xl font-semibold text-foreground group-hover:text-primary transition-colors duration-300">
                  {item.title}
                </CardTitle>
              </CardHeader>
              
              <CardContent className="relative z-10">
                <p className="text-muted-foreground group-hover:text-foreground transition-colors duration-300 mb-4">
                  {item.description}
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
          ))}
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
  );
};

export default TronWelcomeScreen;
