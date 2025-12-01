@echo off
echo.
echo 🚀 Starting docs-pipeline web demo...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Build Docker images
echo 📦 Building Docker images (this may take a few minutes on first run)...
docker-compose build

echo.
echo 🔄 Starting services...
docker-compose up -d

echo.
echo ⏳ Waiting for services to be ready...
timeout /t 5 /nobreak >nul

REM Wait for health check
set MAX_RETRIES=30
set RETRY_COUNT=0

:wait_loop
curl -s http://localhost:8080/health >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if %RETRY_COUNT% LSS %MAX_RETRIES% (
        echo|set /p="."
        timeout /t 2 /nobreak >nul
        goto wait_loop
    ) else (
        echo.
        echo ⚠️ Service didn't start within expected time. Checking logs...
        docker-compose logs
        pause
        exit /b 1
    )
)

echo.
echo ✅ ✅ ✅ Demo is ready! ✅ ✅ ✅
echo.
echo 🌐 Open your browser to: http://localhost:8080
echo.
echo 📝 To stop the demo:
echo    docker-compose down
echo.
echo 📋 To view logs:
echo    docker-compose logs -f
echo.
pause

