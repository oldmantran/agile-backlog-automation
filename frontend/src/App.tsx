import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

// Authentication
import { AuthProvider, RequireAuth } from './contexts/AuthContext';
import AuthScreen from './screens/auth/AuthScreen';

// Screens
import WelcomeScreen from './screens/onboarding/WelcomeScreen';
import MyProjectsScreen from './screens/project/MyProjectsScreen';
import SimpleProjectWizard from './screens/project/SimpleProjectWizard';
import BacklogSweeperScreen from './screens/sweeper/BacklogSweeperScreen';
import BacklogSweeperScreen_new from './screens/sweeper/BacklogSweeperScreen_new';
import TronWelcomeScreen from './screens/TronWelcomeScreen';
import TronConfigScreen from './screens/TronConfigScreen';
import TronExecutableScreen from './screens/TronExecutableScreen';
import TronBacklogSweeperScreen from './screens/TronBacklogSweeperScreen';
import TronCleanupWorkItemsScreen from './screens/TronCleanupWorkItemsScreen';
import TronCleanupTestCasesScreen from './screens/TronCleanupTestCasesScreen';
import TronSettingsScreen from './screens/settings/TronSettingsScreen';
import ConfigureEnvironmentScreen from './screens/settings/ConfigureEnvironmentScreen';
import SearchDocumentationScreen from './screens/search/SearchDocumentationScreen';
import TestCasesCleanupScreen from './screens/cleanup/TestCasesCleanupScreen';
import WorkItemsCleanupScreen from './screens/cleanup/WorkItemsCleanupScreen';
import TestCasesCleanupScreen_NEW from './screens/cleanup/TestCasesCleanupScreen_NEW';
import WorkItemsCleanupScreen_NEW from './screens/cleanup/WorkItemsCleanupScreen_NEW';
import TestScreen from './screens/TestScreen';

function App() {
  return (
    <AuthProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <div className="min-h-screen bg-background">
          <Routes>
            {/* Authentication Routes */}
            <Route path="/login" element={<AuthScreen initialMode="login" />} />
            <Route path="/register" element={<AuthScreen initialMode="register" />} />
            
            {/* Protected Routes */}
            <Route path="/" element={
              <RequireAuth fallback={<AuthScreen />}>
                <TronWelcomeScreen />
              </RequireAuth>
            } />
            <Route path="/dashboard" element={
              <RequireAuth fallback={<AuthScreen />}>
                <TronWelcomeScreen />
              </RequireAuth>
            } />
          
          {/* Welcome/Onboarding - Keep public for now */}
          <Route path="/welcome" element={<WelcomeScreen />} />
          
          {/* Protected Project Management */}
          <Route path="/my-projects" element={
            <RequireAuth fallback={<AuthScreen />}>
              <MyProjectsScreen />
            </RequireAuth>
          } />
          <Route path="/simple-project-wizard" element={
            <RequireAuth fallback={<AuthScreen />}>
              <SimpleProjectWizard />
            </RequireAuth>
          } />
          <Route path="/project/create" element={
            <RequireAuth fallback={<AuthScreen />}>
              <SimpleProjectWizard />
            </RequireAuth>
          } />
          <Route path="/project/new" element={
            <RequireAuth fallback={<AuthScreen />}>
              <SimpleProjectWizard />
            </RequireAuth>
          } />
          
          {/* Protected Backlog Management */}
          <Route path="/backlog-sweeper" element={
            <RequireAuth fallback={<AuthScreen />}>
              <BacklogSweeperScreen />
            </RequireAuth>
          } />
          <Route path="/backlog-sweeper-new" element={
            <RequireAuth fallback={<AuthScreen />}>
              <BacklogSweeperScreen_new />
            </RequireAuth>
          } />
          <Route path="/sweeper" element={
            <RequireAuth fallback={<AuthScreen />}>
              <BacklogSweeperScreen />
            </RequireAuth>
          } />
          
          {/* Protected TRON Interface */}
          <Route path="/tron" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronWelcomeScreen />
            </RequireAuth>
          } />
          <Route path="/tron/config" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronConfigScreen />
            </RequireAuth>
          } />
          <Route path="/tron/executable" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronExecutableScreen />
            </RequireAuth>
          } />
          <Route path="/tron/backlog-sweeper" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronBacklogSweeperScreen />
            </RequireAuth>
          } />
          <Route path="/tron/cleanup-work-items" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronCleanupWorkItemsScreen />
            </RequireAuth>
          } />
          <Route path="/tron/cleanup-test-cases" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronCleanupTestCasesScreen />
            </RequireAuth>
          } />
          <Route path="/tron/settings" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronSettingsScreen />
            </RequireAuth>
          } />
          
          {/* Protected Cleanup Tools */}
          <Route path="/cleanup/test-cases" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TestCasesCleanupScreen />
            </RequireAuth>
          } />
          <Route path="/cleanup/work-items" element={
            <RequireAuth fallback={<AuthScreen />}>
              <WorkItemsCleanupScreen />
            </RequireAuth>
          } />
          <Route path="/cleanup/test-cases-new" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TestCasesCleanupScreen_NEW />
            </RequireAuth>
          } />
          <Route path="/cleanup/work-items-new" element={
            <RequireAuth fallback={<AuthScreen />}>
              <WorkItemsCleanupScreen_NEW />
            </RequireAuth>
          } />
          <Route path="/cleanup/workitems" element={
            <RequireAuth fallback={<AuthScreen />}>
              <WorkItemsCleanupScreen />
            </RequireAuth>
          } />
          <Route path="/cleanup/testcases" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TestCasesCleanupScreen />
            </RequireAuth>
          } />
          
          {/* Protected Search */}
          <Route path="/search" element={
            <RequireAuth fallback={<AuthScreen />}>
              <SearchDocumentationScreen />
            </RequireAuth>
          } />
          
          {/* Protected Settings */}
          <Route path="/settings" element={
            <RequireAuth fallback={<AuthScreen />}>
              <TronSettingsScreen />
            </RequireAuth>
          } />
          <Route path="/configure" element={
            <RequireAuth fallback={<AuthScreen />}>
              <ConfigureEnvironmentScreen />
            </RequireAuth>
          } />
          <Route path="/configure-environment" element={
            <RequireAuth fallback={<AuthScreen />}>
              <ConfigureEnvironmentScreen />
            </RequireAuth>
          } />
          
          {/* Test - Keep public for testing */}
          <Route path="/test" element={<TestScreen />} />
          
          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
    </AuthProvider>
  );
}

export default App;
