#!/usr/bin/env python3
"""
Development server startup script.
Starts both the FastAPI backend and React frontend development servers.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "api_server.py"
    ], cwd=Path(__file__).parent)
    return backend_process

def find_npm_command():
    """Find the npm command, trying different possible locations."""
    possible_commands = ["npm", "npm.cmd"]
    
    # Try standard npm command first
    for cmd in possible_commands:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Try common Node.js installation paths on Windows
    if os.name == 'nt':  # Windows
        possible_paths = [
            os.path.expanduser("~\\AppData\\Roaming\\npm\\npm.cmd"),
            "C:\\Program Files\\nodejs\\npm.cmd",
            "C:\\Program Files (x86)\\nodejs\\npm.cmd",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    return None

def start_frontend():
    """Start the React frontend development server."""
    print("🚀 Starting React frontend server...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Find npm command
    npm_cmd = find_npm_command()
    if not npm_cmd:
        print("❌ Error: npm not found. Please install Node.js and npm.")
        print("   Download from: https://nodejs.org/")
        return None
    
    print(f"✅ Found npm at: {npm_cmd}")
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            return None
    
    try:
        frontend_process = subprocess.Popen([
            npm_cmd, "start"
        ], cwd=frontend_dir)
        return frontend_process
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main function to start both servers."""
    print("🎯 Agile Backlog Automation - Development Server Startup")
    print("=" * 60)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend_process = start_frontend()
        
        if not frontend_process:
            print("❌ Failed to start frontend server")
            if backend_process:
                backend_process.terminate()
            return 1
        
        print("\n✅ Both servers started successfully!")
        print("📡 Backend API: http://localhost:8000")
        print("🌐 Frontend: http://localhost:3000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop both servers")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        print("✅ Servers stopped successfully")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
