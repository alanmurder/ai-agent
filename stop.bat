@echo off
REM AI Agent 停止脚本
REM 停止所有前后端服务

echo.
echo ================================
echo   AI Agent 停止脚本
echo ================================
echo.

REM 停止 Python 后端进程
echo [后端] 停止 Python 服务...
taskkill /FI "WINDOWTITLE eq AI Agent Backend*" /F > nul 2>&1

REM 停止 Node.js 前端进程
echo [前端] 停止 Vite 服务...
taskkill /FI "WINDOWTITLE eq AI Agent Frontend*" /F > nul 2>&1
taskkill /IM "node.exe" /F > nul 2>&1

echo.
echo 所有服务已停止
echo.