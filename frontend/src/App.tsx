import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

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
import SearchDocumentationScreen from './screens/search/SearchDocumentationScreen';
import TestCasesCleanupScreen from './screens/cleanup/TestCasesCleanupScreen';
import WorkItemsCleanupScreen from './screens/cleanup/WorkItemsCleanupScreen';
import TestCasesCleanupScreen_NEW from './screens/cleanup/TestCasesCleanupScreen_NEW';
import WorkItemsCleanupScreen_NEW from './screens/cleanup/WorkItemsCleanupScreen_NEW';
import MainDashboard from './screens/dashboard/MainDashboard';
import MainDashboard_NEW from './screens/dashboard/MainDashboard_NEW';
import TestScreen from './screens/TestScreen';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Routes>
          {/* Main Dashboard as root */}
          <Route path="/" element={<MainDashboard />} />
          
          {/* Welcome/Onboarding */}
          <Route path="/welcome" element={<WelcomeScreen />} />
          
          {/* Project Management */}
          <Route path="/my-projects" element={<MyProjectsScreen />} />
          <Route path="/simple-project-wizard" element={<SimpleProjectWizard />} />
          <Route path="/project/create" element={<SimpleProjectWizard />} />
          <Route path="/project/new" element={<SimpleProjectWizard />} />
          
          {/* Backlog Management */}
          <Route path="/backlog-sweeper" element={<BacklogSweeperScreen />} />
          <Route path="/backlog-sweeper-new" element={<BacklogSweeperScreen_new />} />
          <Route path="/sweeper" element={<BacklogSweeperScreen />} />
          
          {/* TRON Interface */}
          <Route path="/tron" element={<TronWelcomeScreen />} />
          <Route path="/tron/config" element={<TronConfigScreen />} />
          <Route path="/tron/executable" element={<TronExecutableScreen />} />
          <Route path="/tron/backlog-sweeper" element={<TronBacklogSweeperScreen />} />
          <Route path="/tron/cleanup-work-items" element={<TronCleanupWorkItemsScreen />} />
          <Route path="/tron/cleanup-test-cases" element={<TronCleanupTestCasesScreen />} />
          <Route path="/tron/settings" element={<TronSettingsScreen />} />
          
          {/* Cleanup Tools */}
          <Route path="/cleanup/test-cases" element={<TestCasesCleanupScreen />} />
          <Route path="/cleanup/work-items" element={<WorkItemsCleanupScreen />} />
          <Route path="/cleanup/test-cases-new" element={<TestCasesCleanupScreen_NEW />} />
          <Route path="/cleanup/work-items-new" element={<WorkItemsCleanupScreen_NEW />} />
          <Route path="/cleanup/workitems" element={<WorkItemsCleanupScreen />} />
          <Route path="/cleanup/testcases" element={<TestCasesCleanupScreen />} />
          
          {/* Dashboard */}
          <Route path="/dashboard" element={<MainDashboard />} />
          <Route path="/dashboard-new" element={<MainDashboard_NEW />} />
          
          {/* Search */}
          <Route path="/search" element={<SearchDocumentationScreen />} />
          
          {/* Settings */}
          <Route path="/settings" element={<TronSettingsScreen />} />
          
          {/* Test */}
          <Route path="/test" element={<TestScreen />} />
          
          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
