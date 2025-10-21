@echo off
REM ===========================================
REM IKB Navigator - Windows Setup Script
REM ===========================================
REM This script automates the setup process for IKB Navigator on Windows

echo.
echo 🧠 IKB Navigator - Automated Setup
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ and try again.
    pause
    exit /b 1
)

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed. Please install Git and try again.
    pause
    exit /b 1
)

echo [SUCCESS] All prerequisites are installed!
echo.

REM Setup backend
echo [INFO] Setting up backend (FastAPI)...
cd apps\api

echo [INFO] Creating Python virtual environment...
python -m venv venv

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [SUCCESS] Backend setup complete!
cd ..\..

REM Setup frontend
echo [INFO] Setting up frontend (Next.js)...
cd apps\web

echo [INFO] Installing Node.js dependencies...
npm install

echo [SUCCESS] Frontend setup complete!
cd ..\..

REM Setup environment file
echo [INFO] Setting up environment configuration...
if not exist "apps\.env" (
    if exist "apps\.env.example" (
        copy "apps\.env.example" "apps\.env"
        echo [SUCCESS] Created .env file from example
        echo [WARNING] Please edit apps\.env with your actual API keys and credentials
    ) else (
        echo [ERROR] .env.example file not found. Please create apps\.env manually
    )
) else (
    echo [WARNING] .env file already exists. Skipping creation.
)

echo.
echo [SUCCESS] 🎉 Setup complete!
echo.
echo [INFO] Next steps:
echo 1. Edit apps\.env with your API keys and credentials
echo 2. Set up your Supabase database (run migrations)
echo 3. Configure Google Drive API access
echo 4. Start the backend: cd apps\api ^&^& venv\Scripts\activate ^&^& python -m api.main
echo 5. Start the frontend: cd apps\web ^&^& npm run dev
echo.
echo [INFO] For detailed instructions, see README.md
echo.
pause
