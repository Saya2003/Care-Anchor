@echo off
echo Installing file attachment dependencies...
echo.
echo This will install:
echo - pypdf2 (for PDF reading)
echo - python-docx (for Word document reading)
echo.
pause

pip install pypdf2 python-docx

echo.
echo Installation complete!
echo.
echo Please restart your backend server:
echo   python -m uvicorn backend.main:app --reload --port 8000
echo.
pause
