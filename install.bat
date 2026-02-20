@echo off
echo Installing Geoclaw Enterprise...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo Done! Run start_geoclaw.bat to begin.
