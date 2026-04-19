@echo off
REM AI Agent 启动脚本
REM 同时启动前端和后端服务

echo.
echo ================================
echo   AI Agent 启动脚本
echo ================================
echo.

REM 获取项目目录
set PROJECT_ROOT=%~dp0

REM 检查参数
if "%1"=="backend" goto backend_only
if "%1"=="frontend" goto frontend_only

REM 启动后端（新窗口）
echo [后端] 启动 Python 服务...
start "AI Agent Backend" cmd /k "cd /d %PROJECT_ROOT% && venv\Scripts\python.exe -m gateway.server"
echo [后端] 服务启动中... (端口 8080)

REM 等待 2 秒
timeout /t 2 /nobreak > nul

REM 启动前端（新窗口）
echo [前端] 启动 Vite 服务...
start "AI Agent Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"
echo [前端] 服务启动中... (端口 3000)

echo.
echo ================================
echo   服务已启动:
echo   - 后端 API: http://localhost:8080
echo   - 前端界面: http://localhost:3000
echo ================================
echo.
echo 关闭此窗口不会停止服务
echo 如需停止，请关闭后端/前端窗口
echo.

goto end

:backend_only
echo [后端] 启动 Python 服务...
start "AI Agent Backend" cmd /k "cd /d %PROJECT_ROOT% && venv\Scripts\python.exe -m gateway.server"
echo [后端] 服务启动中... (端口 8080)
goto end

:frontend_only
echo [前端] 启动 Vite 服务...
start "AI Agent Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"
echo [前端] 服务启动中... (端口 3000)
goto end

:end