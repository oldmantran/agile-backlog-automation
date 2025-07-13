import React from 'react';
import {
  FiHome,
  FiPlus,
  FiList,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
} from 'react-icons/fi';
import { NavLink as RouterLink, useLocation } from 'react-router-dom';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { cn } from '../../lib/utils';

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
  const isActive = location.pathname === to;
  
  return (
    <Button
      asChild
      variant="ghost"
      className={cn(
        "w-full justify-start h-auto py-3 pl-4 border-l-4 border-l-transparent rounded-none",
        isActive && "bg-primary/10 border-l-primary text-primary font-semibold"
      )}
    >
      <RouterLink to={to}>
        <Icon className="mr-3 h-5 w-5" />
        {children}
      </RouterLink>
    </Button>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
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
          <NavItem icon={FiPlus} to="/project/new">
            Create New Project
          </NavItem>
          <NavItem icon={FiList} to="/projects">
            My Projects
          </NavItem>
          
          <div className="pt-4 pb-2">
            <Separator />
          </div>
          
          <NavItem icon={FiSettings} to="/settings">
            Settings
          </NavItem>
          <NavItem icon={FiHelpCircle} to="/help">
            Help & Support
          </NavItem>
        </div>
        
        <Button
          variant="ghost"
          className="w-full justify-start pl-4 rounded-none"
        >
          <FiLogOut className="mr-3 h-5 w-5" />
          Sign Out
        </Button>
      </div>
    </div>
  );
};

export default Sidebar;
