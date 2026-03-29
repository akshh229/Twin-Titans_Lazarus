@echo off
cd /d "E:\Project Lazarus"
if not exist "frontend" mkdir frontend
if not exist "frontend\src" mkdir frontend\src
if not exist "frontend\src\api" mkdir frontend\src\api
if not exist "frontend\src\components" mkdir frontend\src\components
if not exist "frontend\src\types" mkdir frontend\src\types
if not exist "frontend\src\styles" mkdir frontend\src\styles
if not exist "frontend\public" mkdir frontend\public
echo Directories created successfully!
