#!/usr/bin/env powershell
# Kill Development Processes Script
# Kills all processes running on ports 8000 and 3000

Write-Host "🔍 Scanning for processes on ports 8000 and 3000..." -ForegroundColor Yellow

# Function to kill processes on a specific port
function Kill-ProcessOnPort {
    param(
        [int]$Port
    )
    
    Write-Host "Checking port $Port..." -ForegroundColor Cyan
    
    # Get processes using the port
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    
    if ($processes) {
        foreach ($processId in $processes) {
            try {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "  🔥 Killing process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Red
                    Stop-Process -Id $processId -Force
                    Write-Host "  ✅ Process killed successfully" -ForegroundColor Green
                }
            }
            catch {
                Write-Host "  ❌ Failed to kill process $processId : $_" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "  ✅ No processes found on port $Port" -ForegroundColor Green
    }
}

# Kill processes on port 8000 (backend)
Kill-ProcessOnPort -Port 8000

# Kill processes on port 3000 (frontend)
Kill-ProcessOnPort -Port 3000

# Additional cleanup - kill common development processes
Write-Host "`n🧹 Additional cleanup..." -ForegroundColor Yellow

# Kill Python processes that might be running the server
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        # Check if it's related to our project (basic check)
        $procPath = ""
        try {
            $procPath = $proc.Path
        }
        catch {
            $procPath = ""
        }
        
        if ($procPath -like "*agile-backlog-automation*") {
            Write-Host "  🔥 Killing Python process: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
            Stop-Process -Id $proc.Id -Force
        }
    }
}

# Kill Node processes that might be running React dev server
$nodeProcesses = Get-Process -Name "node*" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    foreach ($proc in $nodeProcesses) {
        # Basic check for Node processes on our ports
        Write-Host "  🔥 Killing Node process: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n🎯 Port cleanup complete!" -ForegroundColor Green
Write-Host "Ports 8000 and 3000 should now be free for fresh testing." -ForegroundColor Green
