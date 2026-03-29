from pathlib import Path

# Create the seed_data directory
seed_dir = Path(r'E:\Project Lazarus\backend\seed_data')
seed_dir.mkdir(parents=True, exist_ok=True)
print(f"Created: {seed_dir}")
