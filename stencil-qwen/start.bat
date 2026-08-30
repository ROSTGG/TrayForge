@echo off
REM Quick start script for Gerber Stencil Generator Web Application (Windows)

echo.
echo 🚀 Starting Gerber Stencil Generator...
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo ✓ Docker and Docker Compose found
echo.

echo 📦 Building Docker images (this may take a few minutes on first run)...
docker-compose up --build

echo.
echo ✅ Application is ready!
echo 📂 Open your browser and navigate to: http://localhost
echo.
echo To stop the application, press Ctrl+C
echo To stop and remove containers: docker-compose down
pause
