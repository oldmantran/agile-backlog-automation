#!/usr/bin/env powershell
# Improved Kill Development Processes Script
# Safely kills development processes with better targeting and confirmation

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host " Improved Development Process Manager" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a process is related to our project
function Test-ProcessIsProjectRelated {
    param([System.Diagnostics.Process]$Process)
    
    try {
        $procPath = $Process.Path
        if (-not $procPath) { return $false }
        
        # Check if process is in our project directory or node_modules
        $projectPatterns = @(
            "*agile-backlog-automation*",
            "*node_modules*",
            "*\.venv*",
            "*\venv*"
        )
        
        foreach ($pattern in $projectPatterns) {
            if ($procPath -like $pattern) {
                return $true
            }
        }
        
        # Check command line arguments for project-related processes
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($Process.Id)").CommandLine
            if ($cmdLine -like "*agile-backlog-automation*" -or 
                $cmdLine -like "*python*api_server*" -or
                $cmdLine -like "*python*tron_api_server*" -or
                $cmdLine -like "*npm*start*" -or
                $cmdLine -like "*node*react*") {
                return $true
            }
        } catch {
            # If we can't get command line, continue
        }
        
        return $false
    } catch {
        return $false
    }
}

# Function to kill processes on a specific port with confirmation
function Stop-ProcessOnPort {
    param([int]$Port)
    
    Write-Host "Checking port $Port..." -ForegroundColor Cyan
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        
        if ($processes) {
            $processesToKill = @()
            
            foreach ($processId in $processes) {
                try {
                    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    if ($process) {
                        $processesToKill += @{
                            Process = $process
                            Reason = "Using port $Port"
                        }
                    }
                } catch {
                    Write-Host "  ⚠️ Could not access process $processId" -ForegroundColor Yellow
                }
            }
            
            if ($processesToKill.Count -gt 0) {
                Write-Host "  Found $($processesToKill.Count) process(es) on port $Port:" -ForegroundColor Yellow
                foreach ($procInfo in $processesToKill) {
                    $proc = $procInfo.Process
                    $reason = $procInfo.Reason
                    Write-Host "    - $($proc.ProcessName) (PID: $($proc.Id)) - $reason" -ForegroundColor White
                }
                
                $response = Read-Host "  Kill these processes? [y/N]"
                if ($response -eq "y" -or $response -eq "Y") {
                    foreach ($procInfo in $processesToKill) {
                        $proc = $procInfo.Process
                        try {
                            Write-Host "    🔥 Killing $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
                            Stop-Process -Id $proc.Id -Force
                            Write-Host "    ✅ Process killed successfully" -ForegroundColor Green
                        } catch {
                            Write-Host "    ❌ Failed to kill process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }
                } else {
                    Write-Host "    ⏭️ Skipping port $Port processes" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "  ✅ No processes found on port $Port" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ❌ Error checking port $Port : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to safely kill project-related processes
function Stop-ProjectProcesses {
    param([string]$ProcessType)
    
    Write-Host "`n🧹 Checking for $ProcessType processes..." -ForegroundColor Yellow
    
    try {
        $processes = Get-Process -Name "$ProcessType*" -ErrorAction SilentlyContinue
        $projectProcesses = @()
        
        if ($processes) {
            foreach ($proc in $processes) {
                if (Test-ProcessIsProjectRelated -Process $proc) {
                    $projectProcesses += $proc
                }
            }
            
            if ($projectProcesses.Count -gt 0) {
                Write-Host "  Found $($projectProcesses.Count) project-related $ProcessType process(es):" -ForegroundColor Yellow
                foreach ($proc in $projectProcesses) {
                    Write-Host "    - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor White
                }
                
                $response = Read-Host "  Kill these $ProcessType processes? [y/N]"
                if ($response -eq "y" -or $response -eq "Y") {
                    foreach ($proc in $projectProcesses) {
                        try {
                            Write-Host "    🔥 Killing $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
                            Stop-Process -Id $proc.Id -Force
                            Write-Host "    ✅ $ProcessType process killed successfully" -ForegroundColor Green
                        } catch {
                            Write-Host "    ❌ Failed to kill $ProcessType process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }
                } else {
                    Write-Host "    ⏭️ Skipping $ProcessType processes" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ✅ No project-related $ProcessType processes found" -ForegroundColor Green
            }
        } else {
            Write-Host "  ✅ No $ProcessType processes found" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ❌ Error checking $ProcessType processes: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main execution
Write-Host "🔍 Scanning for development processes..." -ForegroundColor Yellow

# Check for confirmation before proceeding
Write-Host "`n⚠️ This script will help you kill development processes." -ForegroundColor Yellow
Write-Host "   It will ask for confirmation before killing each group of processes." -ForegroundColor Yellow
$globalConfirm = Read-Host "`nContinue? [y/N]"

if ($globalConfirm -ne "y" -and $globalConfirm -ne "Y") {
    Write-Host "`n❌ Operation cancelled by user." -ForegroundColor Red
    exit 0
}

# Kill processes on port 8000 (backend)
Stop-ProcessOnPort -Port 8000

# Kill processes on port 3000 (frontend)
Stop-ProcessOnPort -Port 3000

# Kill project-related Python processes
Stop-ProjectProcesses -ProcessType "python"

# Kill project-related Node processes
Stop-ProjectProcesses -ProcessType "node"

# Additional cleanup for common development processes
Write-Host "`n🔧 Additional cleanup..." -ForegroundColor Yellow

# Check for npm processes
try {
    $npmProcesses = Get-Process -Name "npm*" -ErrorAction SilentlyContinue
    if ($npmProcesses) {
        Write-Host "  Found npm processes:" -ForegroundColor Yellow
        foreach ($proc in $npmProcesses) {
            Write-Host "    - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor White
        }
        
        $response = Read-Host "  Kill npm processes? [y/N]"
        if ($response -eq "y" -or $response -eq "Y") {
            foreach ($proc in $npmProcesses) {
                try {
                    Write-Host "    🔥 Killing npm process (PID: $($proc.Id))" -ForegroundColor Red
                    Stop-Process -Id $proc.Id -Force
                    Write-Host "    ✅ npm process killed successfully" -ForegroundColor Green
                } catch {
                    Write-Host "    ❌ Failed to kill npm process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
} catch {
    Write-Host "  ❌ Error checking npm processes: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 Process cleanup complete!" -ForegroundColor Green
Write-Host "Ports 8000 and 3000 should now be free for fresh testing." -ForegroundColor Green

# Final status check
Write-Host "`n📊 Final status check:" -ForegroundColor Cyan

try {
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    $port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    
    if (-not $port8000) {
        Write-Host "  ✅ Port 8000 is free" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Port 8000 still has processes" -ForegroundColor Yellow
    }
    
    if (-not $port3000) {
        Write-Host "  ✅ Port 3000 is free" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Port 3000 still has processes" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Could not check final port status" -ForegroundColor Red
}

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
try {
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} catch {
    # If ReadKey fails, just continue
} 