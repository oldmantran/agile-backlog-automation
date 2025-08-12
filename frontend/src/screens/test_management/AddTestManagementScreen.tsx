import React, { useState } from 'react';
import Header from '../../components/navigation/Header';
import Sidebar from '../../components/navigation/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { TestTube } from 'lucide-react';

const AddTestManagementScreen: React.FC = () => {
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
                  <TestTube className="w-6 h-6" />
                  Add Test Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  This feature is in development. Soon you will be able to generate comprehensive test plans, suites, and cases for existing backlogs using Azure DevOps Test Management APIs.
                </p>
                <div>
                  <Button variant="outline" disabled>
                    Coming soon
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

export default AddTestManagementScreen;


