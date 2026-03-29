"""
Setup script to create Lazarus project directory structure
Run this first: python setup_structure.py
"""
import os
from pathlib import Path

# Base directory
BASE = Path("E:/Project Lazarus")

# All directories to create
DIRECTORIES = [
    # Nginx
    "nginx",
    
    # Backend structure
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/api",
    "backend/app/websocket",
    "backend/app/services",
    "backend/app/utils",
    "backend/app/workers",
    "backend/tests",
    "backend/migrations/versions",
    "backend/seed_data",
    
    # Frontend structure
    "frontend/src/api",
    "frontend/src/components",
    "frontend/src/pages",
    "frontend/src/hooks",
    "frontend/src/types",
    "frontend/src/styles",
    "frontend/public",
]

def main():
    print("Creating Lazarus project directory structure...")
    
    for dir_path in DIRECTORIES:
        full_path = BASE / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    print(f"\n✅ Successfully created {len(DIRECTORIES)} directories")
    print("\nNext steps:")
    print("1. Run: cd 'E:\\Project Lazarus'")
    print("2. Continue with implementation")

if __name__ == "__main__":
    main()
