import React from 'react';

interface WizardLayoutProps {
  children: React.ReactNode;
  title?: string;
  steps?: string[];
  currentStep?: number;
}

const WizardLayout: React.FC<WizardLayoutProps> = ({ 
  children, 
  title = "Wizard", 
  steps = [], 
  currentStep = 0 
}) => {
  return (
    <div className="min-h-screen bg-slate-900 py-8">
      <div className="container mx-auto max-w-4xl px-4">
        {/* Wizard Header */}
        {title && (
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-cyan-100 mb-6">{title}</h1>
            
            {/* Progress Steps */}
            {steps.length > 0 && (
              <div className="flex justify-center items-center space-x-4 mb-8">
                {steps.map((step, index) => (
                  <React.Fragment key={index}>
                    <div className="flex items-center">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                        ${index <= currentStep 
                          ? 'bg-cyan-600 text-white' 
                          : 'bg-slate-700 text-slate-400'
                        }
                      `}>
                        {index + 1}
                      </div>
                      <span className={`
                        ml-2 text-sm font-medium
                        ${index <= currentStep ? 'text-cyan-100' : 'text-slate-400'}
                      `}>
                        {step}
                      </span>
                    </div>
                    {index < steps.length - 1 && (
                      <div className={`
                        w-8 h-px
                        ${index < currentStep ? 'bg-cyan-600' : 'bg-slate-600'}
                      `} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Wizard Content */}
        <div className="flex items-center justify-center">
          {children}
        </div>
      </div>
    </div>
  );
};

export default WizardLayout;
