import React, { useState } from 'react';
import { Box, useDisclosure } from '@chakra-ui/react';
import Header from '../navigation/Header';
import Sidebar from '../navigation/Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  return (
    <Box minH="100vh">
      <Header onMenuClick={onOpen} />
      <Sidebar isOpen={isOpen} onClose={onClose} />
      
      <Box
        ml={{ base: 0, lg: '250px' }}
        pt="70px"
        transition="margin-left 0.3s ease"
      >
        {children}
      </Box>
    </Box>
  );
};

export default MainLayout;
