# Agile Backlog Automation Startup Script (PowerShell)
# This script helps you start the application components

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host " Agile Backlog Automation Startup Script" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found at .venv\Scripts\Activate.ps1" -ForegroundColor Red
    Write-Host "Please ensure you have set up the Python virtual environment first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "What would you like to start?" -ForegroundColor Green
Write-Host "1. Backend Only (Main API Server)" -ForegroundColor White
Write-Host "2. Backend Only (Tron API Server)" -ForegroundColor White
Write-Host "3. Frontend Only" -ForegroundColor White
Write-Host "4. Full Stack (Backend + Frontend)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Starting Main API Server..." -ForegroundColor Green
        Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API documentation at: http://localhost:8000/docs" -ForegroundColor Cyan
        python api_server.py
    }
    "2" {
        Write-Host "Starting Tron API Server..." -ForegroundColor Green
        Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Frontend will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API documentation at: http://localhost:8000/docs" -ForegroundColor Cyan
        python tron_api_server.py
    }
    "3" {
        Write-Host "Starting Frontend Only..." -ForegroundColor Green
        Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "Note: Make sure the backend is running separately!" -ForegroundColor Yellow
        Set-Location frontend
        npm start
    }
    "4" {
        Write-Host "Starting Full Stack (Backend + Frontend)..." -ForegroundColor Green
        Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
        
        # Start backend in background
        Write-Host "Starting backend server..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-Command", "& .venv\Scripts\Activate.ps1; python tron_api_server.py"
        
        # Wait a moment for backend to start
        Start-Sleep -Seconds 3
        
        # Start frontend
        Write-Host "Starting frontend..." -ForegroundColor Yellow
        Set-Location frontend
        npm start
    }
    default {
        Write-Host "Invalid choice. Starting Tron API Server by default..." -ForegroundColor Yellow
        python tron_api_server.py
    }
}

Write-Host ""
Write-Host "Application stopped." -ForegroundColor Red
Read-Host "Press Enter to exit"
