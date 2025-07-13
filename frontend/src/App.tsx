import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Screen imports
import TestScreen from './screens/TestScreen';
// import MainDashboard from './screens/dashboard/MainDashboard';
// import ProjectWizard from './screens/project/ProjectWizard';
// import SimpleProjectWizard from './screens/project/SimpleProjectWizard';
// import NewProjectScreen from './screens/project/NewProjectScreen';
// import WelcomeScreen from './screens/onboarding/WelcomeScreen';
// import WorkItemsCleanupScreen from './screens/cleanup/WorkItemsCleanupScreen';
// import TestCasesCleanupScreen from './screens/cleanup/TestCasesCleanupScreen';
// import BacklogSweeperScreen from './screens/sweeper/BacklogSweeperScreen';
// import SearchDocumentationScreen from './screens/search/SearchDocumentationScreen';

// Layout imports
import MainLayout from './components/layout/MainLayout';
// import WizardLayout from './components/layout/WizardLayout';

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Router>
        <Routes>
          {/* Test route for migration */}
          <Route path="/" element={
            <MainLayout>
              <TestScreen />
            </MainLayout>
          } />
          
          {/* All other routes temporarily commented out for migration testing */}
        </Routes>
      </Router>
    </div>
  );
}

export default App;
