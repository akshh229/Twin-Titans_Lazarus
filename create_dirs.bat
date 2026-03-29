@echo off
cd /d E:\Project Lazarus

mkdir nginx
mkdir backend\app\models
mkdir backend\app\schemas
mkdir backend\app\api
mkdir backend\app\websocket
mkdir backend\app\services
mkdir backend\app\utils
mkdir backend\app\workers
mkdir backend\tests
mkdir backend\migrations\versions
mkdir backend\seed_data
mkdir frontend\src\api
mkdir frontend\src\components
mkdir frontend\src\pages
mkdir frontend\src\hooks
mkdir frontend\src\types
mkdir frontend\src\styles
mkdir frontend\public

echo All directories created successfully
dir /s /b
