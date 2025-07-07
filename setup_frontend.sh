# Installation script for frontend dependencies
# Run this script to set up the React application with all required dependencies

# Navigate to the frontend directory
cd frontend

# Install all dependencies from package.json
npm install

# Create a .env file with default settings
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env

# Success message
echo ""
echo "======================================================"
echo "✅ Frontend setup complete!"
echo "======================================================"
echo ""
echo "To start the development server:"
echo "cd frontend"
echo "npm start"
echo ""
echo "This will launch the application on http://localhost:3000"
