@echo off
echo ================================================
echo   LiveKit Python Agent - Starting
echo ================================================
echo.
echo Make sure .env file is configured!
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the agent
echo Starting agent...
python agent.py dev

pause
