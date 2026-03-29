#!/usr/bin/env python3
"""
Execute setup_seed_data.py and capture output
"""
import sys
sys.path.insert(0, r'E:\Project Lazarus')

# Execute the setup script
with open(r'E:\Project Lazarus\setup_seed_data.py', 'r') as f:
    code = f.read()

try:
    exec(code)
    print("\n✅ Script executed successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
