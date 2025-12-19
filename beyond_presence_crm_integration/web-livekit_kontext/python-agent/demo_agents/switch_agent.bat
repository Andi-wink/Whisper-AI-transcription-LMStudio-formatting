@echo off
REM Change to python-agent directory first
cd /d "%~dp0.."
call .\venv\Scripts\activate

:menu
cls
echo.
echo ========================================
echo   LiveKit Demo Agent Switcher
echo ========================================
echo.
echo   1. Basic Insurance Agent
echo   2. German-Speaking Agent  
echo   3. Avatar Agent (Beyond Presence)
echo   4. Multi-Agent Handoff
echo   5. Exit
echo.
echo   (Previous agent will be stopped automatically)
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto basic
if "%choice%"=="2" goto german
if "%choice%"=="3" goto avatar
if "%choice%"=="4" goto handoff
if "%choice%"=="5" goto end
goto menu

:basic
call :stop_agents
echo Starting Basic Agent...
echo.
echo === Press Ctrl+C to stop, then run this script again to switch ===
echo.
python demo_agents/demo_1_basic.py start
goto menu

:german
call :stop_agents
echo Starting German Agent...
echo.
echo === Press Ctrl+C to stop, then run this script again to switch ===
echo.
python demo_agents/demo_2_german.py start
goto menu

:avatar
call :stop_agents
echo Starting Avatar Agent...
echo.
echo === Press Ctrl+C to stop, then run this script again to switch ===
echo.
python demo_agents/demo_3_avatar.py start
goto menu

:handoff
call :stop_agents
echo Starting Handoff Agent...
echo.
echo === Press Ctrl+C to stop, then run this script again to switch ===
echo.
python demo_agents/demo_4_handoff.py start
goto menu

:stop_agents
echo Stopping any running agents...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
exit /b

:end
call :stop_agents
echo Goodbye!
exit
