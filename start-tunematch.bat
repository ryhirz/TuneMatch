@echo off
REM ============================================================
REM TuneMatch 一键启动（Windows）
REM 用法：双击本文件，或在 cmd 中运行 start-tunematch.bat
REM 启动后：前端 http://localhost:5173  后端 http://localhost:8000
REM ============================================================
chcp 65001 >nul
title TuneMatch · 一键启动

echo.
echo  ========================================
echo   TuneMatch 启动中...
echo   前端 http://localhost:5173
echo   后端 http://localhost:8000
echo  ========================================
echo.

REM 定位到项目根目录（脚本所在目录的上级）
set ROOT=%~dp0
cd /d "%ROOT%"

REM 查找 Python（优先虚拟环境）
set PY=python
if exist "%ROOT%backend\.venv\Scripts\python.exe" set PY=%ROOT%backend\.venv\Scripts\python.exe

REM ---------- 1. 启动后端（独立窗口） ----------
echo [1/2] 启动后端 :8000 ...
start "TuneMatch-Backend" cmd /k "cd /d %ROOT%backend && %PY% -m uvicorn main:app --host 0.0.0.0 --port 8000"

REM 等待后端就绪
echo       等待后端就绪...
timeout /t 4 /nobreak >nul

REM ---------- 2. 启动前端（独立窗口） ----------
echo [2/2] 启动前端 :5173 ...
start "TuneMatch-Frontend" cmd /k "cd /d %ROOT%frontend && npm run dev -- --host 0.0.0.0"

timeout /t 3 /nobreak >nul
echo.
echo  已启动！浏览器打开 http://localhost:5173
echo  关闭前请保持这两个窗口运行。
echo.
pause
