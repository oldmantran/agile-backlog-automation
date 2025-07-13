import React from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';

const TestScreen: React.FC = () => {
  return (
    <div className="container mx-auto p-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl text-primary">Migration Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Test Input</label>
            <Input placeholder="Test shadcn/ui migration" />
          </div>
          
          <div className="flex space-x-4">
            <Button>Primary Button</Button>
            <Button variant="outline">Outline Button</Button>
            <Button variant="secondary">Secondary Button</Button>
          </div>
          
          <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg border-glow">
            <p className="text-sm">
              ✅ Migration working! This component uses shadcn/ui with Tron theme.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TestScreen;
