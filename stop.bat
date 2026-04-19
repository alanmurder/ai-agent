@echo off
REM AI Agent Stop Script
REM Stop all frontend and backend services

echo.
echo ================================
echo   AI Agent Stop Script
echo ================================
echo.

REM Stop Python backend process
echo [Backend] Stopping Python service...
taskkill /FI "WINDOWTITLE eq AI Agent Backend*" /F > nul 2>&1

REM Stop Node.js frontend process
echo [Frontend] Stopping Vite service...
taskkill /FI "WINDOWTITLE eq AI Agent Frontend*" /F > nul 2>&1

echo.
echo All services stopped
echo.