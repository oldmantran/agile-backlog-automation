import React from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Button,
  Text,
  useColorModeValue,
  Divider,
  Icon,
} from '@chakra-ui/react';
import {
  FiHome,
  FiPlus,
  FiList,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
} from 'react-icons/fi';
import { NavLink as RouterLink, useLocation } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItemProps {
  icon: React.ElementType;
  to: string;
  children: React.ReactNode;
}

const NavItem: React.FC<NavItemProps> = ({ icon, to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  const activeBg = useColorModeValue('brand.50', 'whiteAlpha.200');
  const hoverBg = useColorModeValue('gray.100', 'whiteAlpha.100');
  
  return (
    <Button
      as={RouterLink}
      to={to}
      variant="ghost"
      justifyContent="start"
      w="full"
      h="auto"
      py={3}
      pl={4}
      leftIcon={<Icon as={icon} boxSize={5} />}
      bg={isActive ? activeBg : 'transparent'}
      color={isActive ? 'brand.600' : undefined}
      borderLeftWidth={isActive ? 4 : 0}
      borderLeftColor="brand.500"
      _hover={{ bg: hoverBg }}
      borderRadius={0}
    >
      <Text fontWeight={isActive ? 'semibold' : 'normal'}>{children}</Text>
    </Button>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Box
      position="fixed"
      left={0}
      h="full"
      w={{ base: 'full', lg: '250px' }}
      bg={bgColor}
      borderRightWidth="1px"
      borderRightColor={borderColor}
      transform={{ base: isOpen ? 'translateX(0)' : 'translateX(-100%)', lg: 'translateX(0)' }}
      transition="transform 0.3s ease"
      zIndex={20}
      overflowY="auto"
      display={{ base: isOpen ? 'block' : 'none', lg: 'block' }}
    >
      <Flex
        h="full"
        direction="column"
        pt="70px" // Space for header
        pb={6}
      >
        <VStack align="stretch" spacing={1} flex="1">
          <NavItem icon={FiHome} to="/dashboard">
            Dashboard
          </NavItem>
          <NavItem icon={FiPlus} to="/project/new">
            Create New Project
          </NavItem>
          <NavItem icon={FiList} to="/projects">
            My Projects
          </NavItem>
          
          <Box pt={4} pb={2}>
            <Divider />
          </Box>
          
          <NavItem icon={FiSettings} to="/settings">
            Settings
          </NavItem>
          <NavItem icon={FiHelpCircle} to="/help">
            Help & Support
          </NavItem>
        </VStack>
        
        <Button
          variant="ghost"
          justifyContent="start"
          w="full"
          pl={4}
          leftIcon={<Icon as={FiLogOut} boxSize={5} />}
          _hover={{ bg: useColorModeValue('gray.100', 'whiteAlpha.100') }}
          borderRadius={0}
        >
          Sign Out
        </Button>
      </Flex>
    </Box>
  );
};

export default Sidebar;
