@echo off
REM Structurizr CLI Wrapper for Windows
REM Provides easy access to Structurizr CLI via Docker

setlocal enabledelayedexpansion

REM Configuration
set DOCKER_IMAGE=structurizr/cli:latest
set WORKSPACE_DIR=%CD%

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop
    exit /b 1
)

REM Parse command
set COMMAND=%1
if "%COMMAND%"=="" (
    echo Structurizr CLI Wrapper
    echo.
    echo Usage:
    echo   structurizr.bat ^<command^> [options]
    echo.
    echo Commands:
    echo   export      Export diagrams from DSL workspace
    echo   validate    Validate DSL workspace syntax
    echo   serve       Start Structurizr Lite server
    echo   check       Check Docker and Structurizr CLI availability
    echo   help        Show this help message
    echo.
    echo Examples:
    echo   structurizr.bat export --workspace docs/Architecture.dsl --format mermaid --output docs/
    echo   structurizr.bat validate --workspace docs/Architecture.dsl
    echo   structurizr.bat serve --workspace docs/Architecture.dsl
    echo   structurizr.bat check
    echo.
    exit /b 0
)

REM Handle check command
if "%COMMAND%"=="check" (
    echo [INFO] Checking Docker...
    docker --version
    if errorlevel 1 (
        echo [ERROR] Docker not found
        exit /b 1
    )
    
    echo [INFO] Checking Docker is running...
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker is not running
        exit /b 1
    )
    
    echo [INFO] Checking Structurizr CLI image...
    docker images structurizr/cli >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Structurizr CLI image not found, pulling...
        docker pull %DOCKER_IMAGE%
        if errorlevel 1 (
            echo [ERROR] Failed to pull Structurizr CLI image
            exit /b 1
        )
    )
    
    echo [OK] All dependencies available
    exit /b 0
)

REM Handle help command
if "%COMMAND%"=="help" (
    goto :help
)

REM Pull image if not present (for export/validate/serve)
if "%COMMAND%"=="export" goto :pull_image
if "%COMMAND%"=="validate" goto :pull_image
if "%COMMAND%"=="serve" goto :pull_image
goto :run_command

:pull_image
docker images structurizr/cli >nul 2>&1
if errorlevel 1 (
    echo [INFO] Pulling Structurizr CLI image...
    docker pull %DOCKER_IMAGE%
    if errorlevel 1 (
        echo [ERROR] Failed to pull Structurizr CLI image
        exit /b 1
    )
)

:run_command
REM Build Docker command
set DOCKER_CMD=docker run --rm -v "%WORKSPACE_DIR%":/workspace -w /workspace %DOCKER_IMAGE%

REM Handle serve command (needs port mapping)
if "%COMMAND%"=="serve" (
    set DOCKER_CMD=docker run --rm -it -p 8080:8080 -v "%WORKSPACE_DIR%":/usr/local/structurizr/workspace -w /usr/local/structurizr/workspace structurizr/lite
    REM Remove --workspace from arguments (Lite uses workspace directory)
    set ARGS=%*
    set ARGS=!ARGS:--workspace =!
    set ARGS=!ARGS:serve =!
    %DOCKER_CMD% %ARGS%
    exit /b !errorlevel!
)

REM For export and validate, pass all remaining arguments
shift
set ARGS=%*
%DOCKER_CMD% %COMMAND% %ARGS%
exit /b %errorlevel%

:help
echo Structurizr CLI Wrapper - Help
echo.
echo This wrapper provides easy access to Structurizr CLI via Docker.
echo.
echo Commands:
echo.
echo   EXPORT
echo   -----
echo   Export diagrams from DSL workspace to various formats
echo.
echo   Usage:
echo     structurizr.bat export --workspace ^<file.dsl^> --format ^<format^> --output ^<dir^>
echo.
echo   Formats: mermaid, plantuml, png, svg, html, json
echo.
echo   Example:
echo     structurizr.bat export --workspace docs/Architecture.dsl --format mermaid --output docs/
echo.
echo   VALIDATE
echo   -------
echo   Validate DSL workspace syntax
echo.
echo   Usage:
echo     structurizr.bat validate --workspace ^<file.dsl^>
echo.
echo   Example:
echo     structurizr.bat validate --workspace docs/Architecture.dsl
echo.
echo   SERVE
echo   -----
echo   Start Structurizr Lite interactive server
echo.
echo   Usage:
echo     structurizr.bat serve --workspace ^<file.dsl^>
echo.
echo   Example:
echo     structurizr.bat serve --workspace docs/Architecture.dsl
echo.
echo   Access at http://localhost:8080
echo.
echo   CHECK
echo   -----
echo   Check Docker and Structurizr CLI availability
echo.
echo   Usage:
echo     structurizr.bat check
echo.
exit /b 0

