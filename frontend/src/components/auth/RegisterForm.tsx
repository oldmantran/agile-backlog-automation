import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../contexts/AuthContext';
import { FiUser, FiMail, FiLock, FiUserPlus, FiEye, FiEyeOff, FiLoader, FiCheck } from 'react-icons/fi';

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const { register, error, isLoading, clearError } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  const validateForm = () => {
    const errors: {[key: string]: string} = {};

    // Username validation
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters long';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, underscores, and hyphens';
    }

    // Email validation
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else {
      if (formData.password.length < 8) {
        errors.password = 'Password must be at least 8 characters long';
      } else if (!/(?=.*[a-z])/.test(formData.password)) {
        errors.password = 'Password must contain at least one lowercase letter';
      } else if (!/(?=.*[A-Z])/.test(formData.password)) {
        errors.password = 'Password must contain at least one uppercase letter';
      } else if (!/(?=.*\d)/.test(formData.password)) {
        errors.password = 'Password must contain at least one number';
      }
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const getPasswordStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/(?=.*[a-z])/.test(password)) score++;
    if (/(?=.*[A-Z])/.test(password)) score++;
    if (/(?=.*\d)/.test(password)) score++;
    if (/(?=.*[!@#$%^&*])/.test(password)) score++;

    if (score < 2) return { strength: 'weak', color: 'text-red-400', width: '20%' };
    if (score < 3) return { strength: 'fair', color: 'text-yellow-400', width: '40%' };
    if (score < 4) return { strength: 'good', color: 'text-blue-400', width: '60%' };
    if (score < 5) return { strength: 'strong', color: 'text-green-400', width: '80%' };
    return { strength: 'very strong', color: 'text-green-400', width: '100%' };
  };

  const passwordStrength = getPasswordStrength(formData.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    clearError();
    
    // Prepare registration data (exclude confirmPassword)
    const { confirmPassword, ...registrationData } = formData;
    const success = await register(registrationData);
    
    if (success) {
      onSuccess?.();
    }
  };

  const handleChange = (field: keyof typeof formData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
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
            <FiUserPlus className="w-10 h-10 text-primary pulse-glow relative z-10 glow-cyan" />
          </div>
        </div>
        <CardTitle className="text-2xl font-bold text-foreground glow-cyan">
          CREATE ACCOUNT
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Join the system to access all features
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
                placeholder="Choose a username"
                value={formData.username}
                onChange={handleChange('username')}
                className={`pl-10 glow-cyan ${validationErrors.username ? 'border-red-500' : ''}`}
                disabled={isLoading}
              />
            </div>
            {validationErrors.username && (
              <p className="text-sm text-red-400">{validationErrors.username}</p>
            )}
          </div>

          {/* Email Field */}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-foreground font-medium glow-cyan">
              Email Address
            </Label>
            <div className="relative">
              <FiMail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange('email')}
                className={`pl-10 glow-cyan ${validationErrors.email ? 'border-red-500' : ''}`}
                disabled={isLoading}
              />
            </div>
            {validationErrors.email && (
              <p className="text-sm text-red-400">{validationErrors.email}</p>
            )}
          </div>

          {/* Full Name Field (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="full_name" className="text-foreground font-medium glow-cyan">
              Full Name <span className="text-muted-foreground text-xs">(optional)</span>
            </Label>
            <div className="relative">
              <FiUser className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="full_name"
                type="text"
                placeholder="Enter your full name"
                value={formData.full_name}
                onChange={handleChange('full_name')}
                className="pl-10 glow-cyan"
                disabled={isLoading}
              />
            </div>
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
                placeholder="Create a secure password"
                value={formData.password}
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
            
            {/* Password Strength Indicator */}
            {formData.password && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Password strength:</span>
                  <span className={passwordStrength.color}>{passwordStrength.strength}</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-1">
                  <div 
                    className={`h-1 rounded-full transition-all duration-300 ${passwordStrength.color.replace('text-', 'bg-')}`}
                    style={{ width: passwordStrength.width }}
                  />
                </div>
              </div>
            )}
            
            {validationErrors.password && (
              <p className="text-sm text-red-400">{validationErrors.password}</p>
            )}
          </div>

          {/* Confirm Password Field */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-foreground font-medium glow-cyan">
              Confirm Password
            </Label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleChange('confirmPassword')}
                className={`pl-10 pr-10 glow-cyan ${validationErrors.confirmPassword ? 'border-red-500' : ''}`}
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={isLoading}
              >
                {showConfirmPassword ? (
                  <FiEyeOff className="w-4 h-4" />
                ) : (
                  <FiEye className="w-4 h-4" />
                )}
              </Button>
              {formData.confirmPassword && formData.password === formData.confirmPassword && (
                <FiCheck className="absolute right-10 top-1/2 transform -translate-y-1/2 w-4 h-4 text-green-400" />
              )}
            </div>
            {validationErrors.confirmPassword && (
              <p className="text-sm text-red-400">{validationErrors.confirmPassword}</p>
            )}
          </div>

          {/* Register Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary hover:bg-primary/80 text-primary-foreground glow-cyan"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <FiLoader className="w-4 h-4 animate-spin" />
                <span>Creating Account...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <FiUserPlus className="w-4 h-4" />
                <span>CREATE ACCOUNT</span>
              </div>
            )}
          </Button>

          {/* Login Link */}
          {onSwitchToLogin && (
            <div className="text-center pt-4 border-t border-primary/20">
              <p className="text-sm text-muted-foreground">
                Already have an account?{' '}
                <Button
                  type="button"
                  variant="link"
                  className="text-primary hover:text-primary/80 p-0 h-auto glow-cyan"
                  onClick={onSwitchToLogin}
                  disabled={isLoading}
                >
                  Sign In
                </Button>
              </p>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

export default RegisterForm;