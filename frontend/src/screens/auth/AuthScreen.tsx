import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/auth/LoginForm';
import RegisterForm from '../../components/auth/RegisterForm';
import { Grid3X3 } from 'lucide-react';

interface AuthScreenProps {
  initialMode?: 'login' | 'register';
}

const AuthScreen: React.FC<AuthScreenProps> = ({ initialMode = 'login' }) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const navigate = useNavigate();

  const handleSuccess = () => {
    // Redirect to dashboard after successful authentication
    navigate('/');
  };

  const switchToLogin = () => setMode('login');
  const switchToRegister = () => setMode('register');

  return (
    <div className="min-h-screen bg-background tron-grid relative overflow-hidden flex items-center justify-center">
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

      <div className="relative z-10 w-full max-w-md px-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 w-20 h-20 bg-primary/20 rounded-lg blur-xl animate-pulse glow-cyan"></div>
              <Grid3X3 className="w-16 h-16 text-primary pulse-glow relative z-10 glow-cyan" />
              <div className="absolute inset-0 w-16 h-16 border-2 border-primary/50 rounded-lg rotate-45 animate-pulse glow-cyan"></div>
              <div className="absolute inset-0 w-20 h-20 border border-accent/30 rounded-lg rotate-12 animate-pulse glow-cyan" style={{ animationDelay: '0.5s' }}></div>
            </div>
          </div>
          
          <h1 className="text-4xl font-bold text-foreground mb-2 tracking-wider glow-cyan">
            <span className="text-primary glow-cyan">C4i</span>
            <span className="text-accent mx-2 glow-cyan">•</span>
            <span className="text-primary glow-cyan">COMMAND</span>
            <span className="text-accent mx-2 glow-cyan">•</span>
            <span className="text-primary glow-cyan">CENTER</span>
          </h1>
          
          <div className="text-lg font-light text-muted-foreground tracking-widest glow-cyan">
            BACKLOG AUTOMATION PLATFORM
          </div>
        </div>

        {/* Auth Forms */}
        {mode === 'login' ? (
          <LoginForm 
            onSuccess={handleSuccess}
            onSwitchToRegister={switchToRegister}
          />
        ) : (
          <RegisterForm
            onSuccess={handleSuccess}
            onSwitchToLogin={switchToLogin}
          />
        )}

        {/* Footer */}
        <div className="text-center mt-8 text-xs font-mono text-muted-foreground">
          <div className="mb-2">SECURE ACCESS TERMINAL</div>
          <div className="flex items-center justify-center space-x-4">
            <span>ENCRYPTED</span>
            <span>•</span>
            <span>JWT SECURED</span>
            <span>•</span>
            <span>LOCAL DATABASE</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;