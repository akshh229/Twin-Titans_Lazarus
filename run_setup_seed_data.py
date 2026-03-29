"""
Execute setup_seed_data.py
"""
import subprocess
import sys

result = subprocess.run([sys.executable, r'E:\Project Lazarus\setup_seed_data.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
sys.exit(result.returncode)
