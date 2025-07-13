import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import theme from './theme';

// Screen imports
import MainDashboard from './screens/dashboard/MainDashboard';
import ProjectWizard from './screens/project/ProjectWizard';
import SimpleProjectWizard from './screens/project/SimpleProjectWizard';
import NewProjectScreen from './screens/project/NewProjectScreen';
import WelcomeScreen from './screens/onboarding/WelcomeScreen';
import WorkItemsCleanupScreen from './screens/cleanup/WorkItemsCleanupScreen';
import TestCasesCleanupScreen from './screens/cleanup/TestCasesCleanupScreen';
import BacklogSweeperScreen from './screens/sweeper/BacklogSweeperScreen';
import SearchDocumentationScreen from './screens/search/SearchDocumentationScreen';

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
          
          <Route path="/cleanup/work-items" element={
            <MainLayout>
              <WorkItemsCleanupScreen />
            </MainLayout>
          } />
          
          <Route path="/cleanup/test-cases" element={
            <MainLayout>
              <TestCasesCleanupScreen />
            </MainLayout>
          } />
          
          <Route path="/sweeper" element={
            <MainLayout>
              <BacklogSweeperScreen />
            </MainLayout>
          } />
          
          <Route path="/search" element={
            <MainLayout>
              <SearchDocumentationScreen />
            </MainLayout>
          } />
          
          <Route path="/project/create" element={
            <MainLayout>
              <NewProjectScreen />
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
