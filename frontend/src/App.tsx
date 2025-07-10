import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import theme from './theme';

// Screen imports
import MainDashboard from './screens/dashboard/MainDashboard';
import ProjectWizard from './screens/project/ProjectWizard';
import SimpleProjectWizard from './screens/project/SimpleProjectWizard';
import WelcomeScreen from './screens/onboarding/WelcomeScreen';

// Layout imports
import MainLayout from './components/layout/MainLayout';
import WizardLayout from './components/layout/WizardLayout';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<WelcomeScreen />} />
          
          {/* Routes with MainLayout */}
          <Route path="/dashboard" element={
            <MainLayout>
              <MainDashboard />
            </MainLayout>
          } />
          
          {/* Routes with WizardLayout */}
          <Route path="/project/new" element={
            <WizardLayout>
              <SimpleProjectWizard />
            </WizardLayout>
          } />
          
          {/* Legacy full wizard (for reference) */}
          <Route path="/project/wizard" element={
            <WizardLayout>
              <ProjectWizard />
            </WizardLayout>
          } />
        </Routes>
      </Router>
    </ChakraProvider>
  );
}

export default App;
