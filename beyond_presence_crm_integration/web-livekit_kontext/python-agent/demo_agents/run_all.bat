@echo off
echo Starting all 4 demo agents...
echo.

REM Start each agent in a new terminal window
start "Demo 1 - Basic" cmd /k "cd /d %~dp0.. && .\venv\Scripts\activate && python demo_agents/demo_1_basic.py start"
timeout /t 2 >nul

start "Demo 2 - German" cmd /k "cd /d %~dp0.. && .\venv\Scripts\activate && python demo_agents/demo_2_german.py start"
timeout /t 2 >nul

start "Demo 3 - Avatar" cmd /k "cd /d %~dp0.. && .\venv\Scripts\activate && python demo_agents/demo_3_avatar.py start"
timeout /t 2 >nul

start "Demo 4 - Handoff" cmd /k "cd /d %~dp0.. && .\venv\Scripts\activate && python demo_agents/demo_4_handoff.py start"

echo.
echo All agents started!
echo.
echo Connect to each agent using these playground URLs:
echo.
echo Demo 1 (Basic):   https://agents-playground.livekit.io/?tab=connection^&agent=demo-basic
echo Demo 2 (German):  https://agents-playground.livekit.io/?tab=connection^&agent=demo-german
echo Demo 3 (Avatar):  https://agents-playground.livekit.io/?tab=connection^&agent=demo-avatar
echo Demo 4 (Handoff): https://agents-playground.livekit.io/?tab=connection^&agent=demo-handoff
echo.
pause
