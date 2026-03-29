@echo off
echo ========================================
echo LAZARUS - Creating Database Migrations
echo ========================================
echo.

cd /d "%~dp0"
python CREATE_MIGRATIONS_COMPLETE.py

echo.
echo Press any key to exit...
pause >nul
