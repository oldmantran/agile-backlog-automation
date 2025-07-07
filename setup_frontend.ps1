# Installation script for frontend dependencies (Windows PowerShell)
# Run this script to set up the React application with all required dependencies

# Navigate to the frontend directory
Set-Location -Path .\frontend

# Install all dependencies from package.json
Write-Host "Installing frontend dependencies... This may take a few minutes."
npm install

# Create a .env file with default settings
"REACT_APP_API_URL=http://localhost:8000/api" | Out-File -FilePath .\.env -Encoding utf8

# Success message
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "✅ Frontend setup complete!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the development server:"
Write-Host "cd frontend"
Write-Host "npm start"
Write-Host ""
Write-Host "This will launch the application on http://localhost:3000"
