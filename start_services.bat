@echo off
echo ==========================================
echo   Stock Analysis System - Start Services
echo ==========================================
echo.

echo Starting MCP Service...
start "MCP Service" cmd /k "cd mcp_service && python mcp_server.py"

echo Waiting for MCP service to start...
timeout /t 3 >nul

echo Starting Web Service...
echo - Web Service: http://localhost:5000
echo - MCP Service: Running in background
echo.
echo Press Ctrl+C to stop Web service
echo.

cd main_app
python web_app.py

echo.
echo Web service stopped
echo Please manually close MCP service window
pause