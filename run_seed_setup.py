"""
Directly execute the seed data setup by loading and running the setup_seed_data.py module
"""
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project to path
    project_root = Path(r'E:\Project Lazarus')
    sys.path.insert(0, str(project_root))
    
    # Read and execute setup_seed_data.py
    setup_script = project_root / 'setup_seed_data.py'
    
    with open(setup_script, 'r') as f:
        code = compile(f.read(), str(setup_script), 'exec')
        exec(code, {'__name__': '__main__', '__file__': str(setup_script)})
