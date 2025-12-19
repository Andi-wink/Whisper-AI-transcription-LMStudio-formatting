@echo off
echo Creating virtual environment 'venv_local'...
python -m venv venv_local

echo Activating virtual environment...
call venv_local\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip setuptools wheel
pip install fugashi --only-binary=:all:
pip install tokenizers --only-binary=:all:
pip install -r requirements_local.txt
pip install git+https://github.com/myshell-ai/MeloTTS.git --no-deps

echo Installation complete!
echo To run the agent, use: venv_local\Scripts\python local_agent.py dev

