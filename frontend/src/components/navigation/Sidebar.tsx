import React from 'react';
import {
  FiHome,
  FiPlus,
  FiList,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
  FiUser,
} from 'react-icons/fi';
import { 
  Sparkles,
  Plus,
  TestTube,
  RefreshCw,
  Settings
} from 'lucide-react';
import { NavLink as RouterLink, useLocation } from 'react-router-dom';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { cn } from '../../lib/utils';
import { useAuth } from '../../contexts/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItemProps {
  icon: React.ElementType;
  to: string;
  children: React.ReactNode;
}

const NavItem: React.FC<NavItemProps> = ({ icon: Icon, to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to || (to === '/dashboard' && location.pathname === '/');
  
  return (
    <Button
      asChild
      variant="ghost"
      className={cn(
        "w-full justify-start h-auto py-3 pl-4 border-l-4 border-l-transparent rounded-none transition-all duration-300",
        isActive && "bg-primary/15 border-l-primary text-primary font-semibold glow-cyan shadow-[0_0_15px_rgba(6,182,212,0.3)]"
      )}
    >
      <RouterLink to={to}>
        <Icon className={cn("mr-3 h-5 w-5 transition-all duration-300", isActive && "glow-cyan")} />
        <span className={cn("transition-all duration-300", isActive && "glow-cyan")}>
          {children}
        </span>
      </RouterLink>
    </Button>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    onClose(); // Close sidebar after logout
  };

  return (
    <div
      className={cn(
        "fixed left-0 h-full w-full lg:w-[250px] bg-card border-r border-border z-20 overflow-y-auto",
        "transform transition-transform duration-300 ease-in-out",
        "lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full",
        "block lg:block"
      )}
    >
      <div className="flex h-full flex-col pt-[70px] pb-6">
        <div className="flex-1 space-y-1">
          <NavItem icon={FiHome} to="/dashboard">
            Dashboard
          </NavItem>
          
          <div className="pt-4 pb-2">
            <Separator />
          </div>
          
          <NavItem icon={Sparkles} to="/optimize-vision">
            Optimize New Vision
          </NavItem>
          <NavItem icon={Plus} to="/simple-project-wizard">
            Create New Backlog
          </NavItem>
          <NavItem icon={TestTube} to="/add-test-management">
            Add Test Management
          </NavItem>
          <NavItem icon={RefreshCw} to="/sweeper">
            Scan Existing Backlog
          </NavItem>
          <NavItem icon={FiList} to="/my-projects">
            My Projects
          </NavItem>
          
          <div className="pt-4 pb-2">
            <Separator />
          </div>
          
          <NavItem icon={Settings} to="/configure">
            Configure Environment
          </NavItem>
          <NavItem icon={FiSettings} to="/settings">
            Settings
          </NavItem>
          <NavItem icon={FiHelpCircle} to="/help">
            Help & Support
          </NavItem>
        </div>
        
        {/* User Info Section */}
        {user && (
          <div className="px-4 py-2 border-t border-border">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                <FiUser className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              </div>
            </div>
          </div>
        )}
        
        <Button
          variant="ghost"
          className="w-full justify-start pl-4 rounded-none hover:bg-red-500/10 hover:text-red-400"
          onClick={handleLogout}
        >
          <FiLogOut className="mr-3 h-5 w-5" />
          Sign Out
        </Button>
      </div>
    </div>
  );
};

export default Sidebar;
