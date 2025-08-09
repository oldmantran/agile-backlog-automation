import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../contexts/AuthContext';
import { FiUser, FiLock, FiLogIn, FiEye, FiEyeOff, FiLoader } from 'react-icons/fi';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToRegister }) => {
  const { login, error, isLoading, clearError } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  const validateForm = () => {
    const errors: {[key: string]: string} = {};

    if (!credentials.username.trim()) {
      errors.username = 'Username is required';
    }

    if (!credentials.password) {
      errors.password = 'Password is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    clearError();
    const success = await login(credentials);
    
    if (success) {
      onSuccess?.();
    }
  };

  const handleChange = (field: keyof typeof credentials) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials(prev => ({
      ...prev,
      [field]: e.target.value
    }));
    
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  return (
    <Card className="w-full max-w-md tron-card bg-card/50 backdrop-blur-sm border border-primary/30">
      <CardHeader className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="relative">
            <div className="absolute inset-0 w-12 h-12 bg-primary/20 rounded-lg blur-xl animate-pulse glow-cyan"></div>
            <FiLogIn className="w-10 h-10 text-primary pulse-glow relative z-10 glow-cyan" />
          </div>
        </div>
        <CardTitle className="text-2xl font-bold text-foreground glow-cyan">
          SYSTEM LOGIN
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Enter your credentials to access the system
        </p>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Global Error Alert */}
          {error && (
            <Alert className="border-red-500/50 bg-red-500/10">
              <AlertDescription className="text-red-300">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Username Field */}
          <div className="space-y-2">
            <Label htmlFor="username" className="text-foreground font-medium glow-cyan">
              Username
            </Label>
            <div className="relative">
              <FiUser className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={credentials.username}
                onChange={handleChange('username')}
                className={`pl-10 glow-cyan ${validationErrors.username ? 'border-red-500' : ''}`}
                disabled={isLoading}
              />
            </div>
            {validationErrors.username && (
              <p className="text-sm text-red-400">{validationErrors.username}</p>
            )}
          </div>

          {/* Password Field */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-foreground font-medium glow-cyan">
              Password
            </Label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={credentials.password}
                onChange={handleChange('password')}
                className={`pl-10 pr-10 glow-cyan ${validationErrors.password ? 'border-red-500' : ''}`}
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? (
                  <FiEyeOff className="w-4 h-4" />
                ) : (
                  <FiEye className="w-4 h-4" />
                )}
              </Button>
            </div>
            {validationErrors.password && (
              <p className="text-sm text-red-400">{validationErrors.password}</p>
            )}
          </div>

          {/* Login Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <FiLoader className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <FiLogIn className="w-4 h-4" />
                <span>LOGIN</span>
              </div>
            )}
          </Button>

          {/* Register Link */}
          {onSwitchToRegister && (
            <div className="text-center pt-4 border-t border-primary/20">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{' '}
                <Button
                  type="button"
                  variant="link"
                  className="text-primary hover:text-primary/80 p-0 h-auto glow-cyan"
                  onClick={onSwitchToRegister}
                  disabled={isLoading}
                >
                  Create Account
                </Button>
              </p>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

export default LoginForm;