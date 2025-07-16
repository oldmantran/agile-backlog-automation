# Agile Backlog Automation - PowerShell Startup Script
# This script starts the unified API server and optionally the frontend

param(
    [switch]$StartFrontend,
    [switch]$NoBrowser
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Agile Backlog Automation - Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start the unified API server
Write-Host ""
Write-Host "Starting Unified API Server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API documentation at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

if ($StartFrontend) {
    Write-Host "Starting frontend development server..." -ForegroundColor Yellow
    
    # Start frontend in background
    Start-Process powershell -ArgumentList "-Command", "& .venv\Scripts\Activate.ps1; cd frontend; npm start"
    
    # Wait a moment for frontend to start
    Start-Sleep -Seconds 3
    
    # Open browser if not disabled
    if (-not $NoBrowser) {
        Start-Process "http://localhost:3000"
    }
    
    # Start backend
    python unified_api_server.py
} else {
    # Start backend only
    python unified_api_server.py
}

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
