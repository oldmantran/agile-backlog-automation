@echo off
echo Starting Agile Backlog Automation Development Servers
echo ====================================================

echo Installing Python dependencies...
pip install -r requirements.txt

echo Starting development servers...
python start_dev_servers.py

pause
