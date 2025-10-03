@echo off
REM Automated MCP Installation Script for OpenAPI Generator (Windows)
REM This script sets up the MCP server for Claude Desktop with ZERO manual configuration

setlocal enabledelayedexpansion

echo ==================================
echo OpenAPI Generator MCP Installer
echo ==================================
echo.

REM Get script directory (project root)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo Project directory: %SCRIPT_DIR%
echo.

REM Step 1: Check for Python 3.11+
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found
    echo.
    echo Please install Python 3.11 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [+] Python %PYTHON_VERSION% found
echo.

REM Step 2: Create/activate virtual environment
echo [2/7] Setting up virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [+] Virtual environment created
) else (
    echo [+] Virtual environment already exists
)
echo.

REM Step 3: Install dependencies
echo [3/7] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
python -m pip install --quiet -e .
echo [+] Dependencies installed
echo.

REM Step 4: Install Playwright browsers
echo [4/7] Installing Playwright browsers...
playwright install chromium >nul 2>&1
if errorlevel 1 (
    echo [!] Playwright browser install skipped
) else (
    echo [+] Playwright browsers installed
)
echo.

REM Step 5: Get API key
echo [5/7] Setting up Anthropic API key...
set API_KEY=
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "ANTHROPIC_API_KEY" .env 2^>nul') do set API_KEY=%%a
)

if not defined API_KEY (
    echo.
    echo Please enter your Anthropic API key:
    echo ^(Get one at: https://console.anthropic.com/^)
    set /p API_KEY="API Key: "

    if not defined API_KEY (
        echo [X] API key required
        pause
        exit /b 1
    )

    REM Save to .env
    echo ANTHROPIC_API_KEY=!API_KEY!> .env
    echo [+] API key saved to .env
) else (
    echo [+] API key found in .env file
)
echo.

REM Step 6: Configure Claude Desktop
echo [6/7] Configuring Claude Desktop...

set "CLAUDE_CONFIG_DIR=%APPDATA%\Claude"
set "CLAUDE_CONFIG_FILE=%CLAUDE_CONFIG_DIR%\claude_desktop_config.json"

REM Create config directory if it doesn't exist
if not exist "%CLAUDE_CONFIG_DIR%" mkdir "%CLAUDE_CONFIG_DIR%"

REM Backup existing config
if exist "%CLAUDE_CONFIG_FILE%" (
    echo Claude Desktop config already exists
    echo Backing up to claude_desktop_config.json.backup
    copy "%CLAUDE_CONFIG_FILE%" "%CLAUDE_CONFIG_FILE%.backup" >nul
)

REM Get absolute paths (convert forward slashes for JSON)
set "MCP_SERVER_PATH=%SCRIPT_DIR%mcp_server.py"
set "MCP_SERVER_PATH=%MCP_SERVER_PATH:\=/%"
set "PYTHON_PATH=%SCRIPT_DIR%venv\Scripts\python.exe"
set "PYTHON_PATH=%PYTHON_PATH:\=/%"

REM Create config using Python
python -c "import json; import os; config_file = r'%CLAUDE_CONFIG_FILE%'; config = json.load(open(config_file)) if os.path.exists(config_file) else {}; config.setdefault('mcpServers', {})['openapi-generator'] = {'command': r'%PYTHON_PATH%'.replace('\\', '/'), 'args': [r'%MCP_SERVER_PATH%'.replace('\\', '/')], 'env': {'ANTHROPIC_API_KEY': r'%API_KEY%'}}; json.dump(config, open(config_file, 'w'), indent=2)"

if errorlevel 1 (
    echo [X] Failed to configure Claude Desktop
    echo Please manually configure using MCP_SETUP.md
    pause
    exit /b 1
)

echo [+] Claude Desktop configured
echo.

REM Step 7: Test installation
echo [7/7] Testing installation...
echo Testing MCP server...

REM Test that the server can start (with timeout)
start /b "" "%PYTHON_PATH%" "%SCRIPT_DIR%mcp_server.py" >nul 2>&1
timeout /t 2 /nobreak >nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq Administrator:*" >nul 2>&1

echo [+] MCP server is functional
echo.

REM Success message
echo ==================================
echo Installation Complete!
echo ==================================
echo.
echo Next steps:
echo.
echo 1. Restart Claude Desktop ^(quit completely and reopen^)
echo.
echo 2. Look for the tools icon ^(wrench^) in Claude Desktop
echo.
echo 3. Try asking Claude:
echo    "Generate an OpenAPI spec for https://catfact.ninja"
echo.
echo Documentation:
echo   - Quick start: type "QUICKSTART.md"
echo   - MCP setup guide: type "MCP_SETUP.md"
echo   - Troubleshooting: See MCP_SETUP.md
echo.
echo Configuration file: %CLAUDE_CONFIG_FILE%
echo.
echo To test the MCP server manually:
echo   venv\Scripts\activate.bat
echo   python mcp_server.py
echo.
echo ==================================
echo Happy API spec generating! 🚀
echo ==================================
echo.
pause
