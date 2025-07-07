import React from 'react';
import { Box, Container } from '@chakra-ui/react';

interface WizardLayoutProps {
  children: React.ReactNode;
}

const WizardLayout: React.FC<WizardLayoutProps> = ({ children }) => {
  return (
    <Box 
      minH="100vh" 
      bgGradient="linear(to-r, blue.50, purple.50)" 
      py={8}
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Container maxW="container.md">
        {children}
      </Container>
    </Box>
  );
};

export default WizardLayout;
