import React from 'react';
import { FiMenu } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';
import { Button } from '../ui/button';

interface HeaderProps {
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  return (
    <header className="fixed top-0 w-full z-10 bg-background/95 backdrop-blur-sm shadow-sm border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Left side: Menu button and Logo */}
          <div className="flex items-center space-x-4">
            {onMenuClick && (
              <Button
                variant="ghost"
                size="icon"
                className="flex lg:hidden"
                onClick={onMenuClick}
                aria-label="Open menu"
              >
                <FiMenu className="h-5 w-5" />
              </Button>
            )}
            
            <RouterLink to="/" className="flex items-center space-x-2">
              {/* Logo */}
              <div className="bg-primary text-primary-foreground font-bold text-lg p-1 rounded-md w-9 h-9 flex items-center justify-center border-glow glow-cyan">
                BA
              </div>
              <span className="font-bold text-lg hidden md:flex text-primary">
                Backlog Automation
              </span>
            </RouterLink>
          </div>
          
          {/* Right side: Additional controls can be added here */}
          <div className="flex items-center space-x-4">
            {/* Future: Add user menu, notifications, etc. */}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
