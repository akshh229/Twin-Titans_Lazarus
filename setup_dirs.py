import os
from pathlib import Path

base_path = Path(r'E:\Project Lazarus')

directories = [
    'nginx',
    r'backend\app\models',
    r'backend\app\schemas',
    r'backend\app\api',
    r'backend\app\websocket',
    r'backend\app\services',
    r'backend\app\utils',
    r'backend\app\workers',
    r'backend\tests',
    r'backend\migrations\versions',
    r'backend\seed_data',
    r'frontend\src\api',
    r'frontend\src\components',
    r'frontend\src\pages',
    r'frontend\src\hooks',
    r'frontend\src\types',
    r'frontend\src\styles',
    r'frontend\public'
]

for dir_path in directories:
    full_path = base_path / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {dir_path}")

print("\nAll directories created successfully!")
