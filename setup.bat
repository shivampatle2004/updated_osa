@echo off
echo.
echo [1/3] Setting up Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing backend requirements...
pip install -r requirements.txt
cd ..

echo.
echo [2/3] Setting up Frontend...
cd frontend
echo Installing frontend dependencies (using npm)...
npm install
cd ..

echo.
echo [3/3] Setup Complete!
echo You can now start the backend with: cd backend ^&^& python main.py
echo And the frontend with: cd frontend ^&^& npm run dev
echo.
pause
