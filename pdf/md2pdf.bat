@echo off
REM Simple batch wrapper for PDF generation
REM Usage: md2pdf.bat <input.md> [output.pdf]

setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Activate virtual environment if it exists
if exist "%PROJECT_ROOT%\venv-pdf\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\venv-pdf\Scripts\activate.bat"
)

REM Call the Python script with all arguments
python "%SCRIPT_DIR%md2pdf.py" %*

endlocal

