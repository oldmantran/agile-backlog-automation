import React from 'react';

interface WizardLayoutProps {
  children: React.ReactNode;
}

const WizardLayout: React.FC<WizardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-r from-blue-50 to-purple-50 py-8 flex items-center justify-center">
      <div className="container mx-auto max-w-4xl px-4">
        {children}
      </div>
    </div>
  );
};

export default WizardLayout;
