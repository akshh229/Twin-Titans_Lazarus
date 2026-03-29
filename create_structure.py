#!/usr/bin/env python3
import os
from pathlib import Path

base_path = Path(r'E:\Project Lazarus')
os.chdir(base_path)

# Directories to create
directories = [
    'nginx',
    'backend/app/models',
    'backend/app/schemas',
    'backend/app/api',
    'backend/app/websocket',
    'backend/app/services',
    'backend/app/utils',
    'backend/app/workers',
    'backend/tests',
    'backend/migrations/versions',
    'backend/seed_data',
    'frontend/src/api',
    'frontend/src/components',
    'frontend/src/pages',
    'frontend/src/hooks',
    'frontend/src/types',
    'frontend/src/styles',
    'frontend/public',
]

print("Creating directory structure...")
for directory in directories:
    path = base_path / directory
    path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {directory}")

print("\n" + "="*60)
print("Verifying directories exist...")
print("="*60)

all_exist = True
for directory in directories:
    path = base_path / directory
    exists = path.exists() and path.is_dir()
    status = "✓" if exists else "✗"
    print(f"{status} {directory}")
    if not exists:
        all_exist = False

print("="*60)
if all_exist:
    print("✓ All directories created and verified successfully!")
else:
    print("✗ Some directories could not be created")
    exit(1)
