@echo off
REM AI Agent Start Script
REM Start frontend and backend services

echo.
echo ================================
echo   AI Agent Start Script
echo ================================
echo.

REM Get project directory
set PROJECT_ROOT=%~dp0

REM Check parameters
if "%1"=="backend" goto backend_only
if "%1"=="frontend" goto frontend_only

REM Start backend (new window)
echo [Backend] Starting Python service...
start "AI Agent Backend" cmd /k "cd /d %PROJECT_ROOT% && venv\Scripts\python.exe -m gateway.server"
echo [Backend] Service starting... (port 8080)

REM Wait 2 seconds
timeout /t 2 /nobreak > nul

REM Start frontend (new window)
echo [Frontend] Starting Vite service...
start "AI Agent Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"
echo [Frontend] Service starting... (port 3000)

echo.
echo ================================
echo   Services started:
echo   - Backend API: http://localhost:8080
echo   - Frontend UI: http://localhost:3000
echo ================================
echo.
echo Close this window will not stop services
echo To stop, close backend/frontend windows
echo.

goto end

:backend_only
echo [Backend] Starting Python service...
start "AI Agent Backend" cmd /k "cd /d %PROJECT_ROOT% && venv\Scripts\python.exe -m gateway.server"
echo [Backend] Service starting... (port 8080)
goto end

:frontend_only
echo [Frontend] Starting Vite service...
start "AI Agent Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"
echo [Frontend] Service starting... (port 3000)
goto end

:end