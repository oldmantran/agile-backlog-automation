# Agile Backlog Automation Frontend

This is the frontend application for the Agile Backlog Automation system, a mobile-first UI designed for project managers, business analysts, product owners, and other stakeholders to easily create and manage product backlogs.

## Features

- Mobile-first design for accessibility on any device
- Project creation wizard with guided steps
- Azure DevOps integration for backlog management
- AI-powered backlog generation and enhancement
- Dashboard for project tracking and status monitoring

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running (see main project README)

### Installation

1. Install dependencies:
```
npm install
```

2. Start the development server:
```
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Project Structure

```
frontend/
├── public/                # Public assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ui/            # Basic UI components
│   │   ├── forms/         # Form components
│   │   ├── navigation/    # Navigation components
│   │   ├── visualization/ # Data visualization
│   │   └── layout/        # Layout components
│   ├── screens/           # Main application screens
│   ├── services/          # API and service integrations
│   ├── utils/             # Utility functions
│   ├── hooks/             # Custom React hooks
│   ├── contexts/          # React contexts
│   └── types/             # TypeScript type definitions
└── package.json
```

## Available Scripts

- `npm start`: Run the app in development mode
- `npm test`: Launch the test runner
- `npm run build`: Build the app for production
- `npm run eject`: Eject from Create React App

## Integration with Azure DevOps

This frontend connects to Azure DevOps through our custom backend API to:

1. Fetch project, area, and iteration information
2. Generate backlog items using AI
3. Create and manage work items
4. Monitor generation progress

## Contributing

See the main repository's CONTRIBUTING.md for guidelines.
