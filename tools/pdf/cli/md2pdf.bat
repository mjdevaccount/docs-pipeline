@echo off
REM Simple batch wrapper for PDF generation
REM Usage: md2pdf.bat <input.md> [output.pdf]

setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PDF_DIR=%SCRIPT_DIR%.."

REM Activate virtual environment if it exists
if exist "%PDF_DIR%\venv-pdf\Scripts\activate.bat" (
    call "%PDF_DIR%\venv-pdf\Scripts\activate.bat"
)

REM Call CLI main.py with all arguments
python "%SCRIPT_DIR%main.py" %*

endlocal

