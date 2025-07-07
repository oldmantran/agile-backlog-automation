import React from 'react';
import {
  Box,
  Container,
  Flex,
  HStack,
  IconButton,
  useColorMode,
  useColorModeValue,
  Image,
  Text,
} from '@chakra-ui/react';
import { FiMenu, FiMoon, FiSun } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';

interface HeaderProps {
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Box 
      as="header" 
      position="fixed" 
      top={0} 
      width="full" 
      zIndex={10}
      bg={bgColor}
      boxShadow="sm"
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
    >
      <Container maxW="container.xl" px={4}>
        <Flex h={16} alignItems="center" justifyContent="space-between">
          {/* Left side: Menu button and Logo */}
          <HStack spacing={4}>
            {onMenuClick && (
              <IconButton
                aria-label="Open menu"
                variant="ghost"
                icon={<FiMenu fontSize="1.25rem" />}
                onClick={onMenuClick}
                display={{ base: 'flex', lg: 'none' }}
              />
            )}
            
            <RouterLink to="/">
              <HStack spacing={2}>
                {/* Logo placeholder - replace with your actual logo */}
                <Box 
                  bg="brand.500" 
                  color="white" 
                  fontWeight="bold" 
                  fontSize="lg"
                  p={1}
                  borderRadius="md"
                  width="36px"
                  height="36px"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  BA
                </Box>
                <Text 
                  fontWeight="bold" 
                  fontSize="lg" 
                  display={{ base: 'none', md: 'flex' }}
                >
                  Backlog Automation
                </Text>
              </HStack>
            </RouterLink>
          </HStack>
          
          {/* Right side: Color mode toggle */}
          <HStack spacing={4}>
            <IconButton
              aria-label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}
              variant="ghost"
              icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
              onClick={toggleColorMode}
            />
          </HStack>
        </Flex>
      </Container>
    </Box>
  );
};

export default Header;
