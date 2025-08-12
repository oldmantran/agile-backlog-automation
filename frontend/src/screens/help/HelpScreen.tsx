import React, { useState } from 'react';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { FiHelpCircle } from 'react-icons/fi';

const HelpScreen: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="ml-0 lg:ml-[250px] pt-[70px] transition-all duration-300 ease-in-out">
        <div className="min-h-screen bg-background tron-grid relative overflow-hidden p-6">
          <div className="max-w-4xl mx-auto">
            <Card className="tron-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <FiHelpCircle className="w-6 h-6" />
                  Help & Support
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Need assistance? Check the documentation in the repo under <code>docs/</code>, or contact your project admin.
                </p>
                <div className="flex gap-3">
                  <Button asChild>
                    <a href="/docs/VISION_OPTIMIZATION_GUIDE.md" target="_blank" rel="noreferrer">Vision Optimization Guide</a>
                  </Button>
                  <Button variant="outline" asChild>
                    <a href="/README.md" target="_blank" rel="noreferrer">README</a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpScreen;


