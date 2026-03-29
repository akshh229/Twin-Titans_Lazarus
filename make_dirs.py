import os
from pathlib import Path

# Create all necessary directories
BASE_DIR = Path(__file__).parent
dirs = [
    "backend/migrations/versions"
]

for d in dirs:
    (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
    print(f"Created: {d}")

print("\nDirectories created successfully!")
