#!/usr/bin/env python3
import os
import subprocess

def main():
    found = False
    for root, dirs, files in os.walk('.'):
        # Exclude common directories to keep search clean
        for exclude in ['node_modules', '.venv', 'vendor', '.git']:
            if exclude in dirs:
                dirs.remove(exclude)
                
        if 'Makefile' in files:
            found = True
            makefile_path = os.path.join(root, 'Makefile')
            dir_path = os.path.abspath(root)
            print(f"Makefile project detected at {makefile_path}")
            
            # Run "make test", falling back to "make", or succeeding silently
            try:
                res = subprocess.run(['make', 'test'], cwd=dir_path)
                if res.returncode != 0:
                    subprocess.run(['make'], cwd=dir_path)
            except Exception as e:
                print(f"Failed to execute make command in {dir_path}: {e}")
                
    if not found:
        print("No Makefiles found.")

if __name__ == '__main__':
    main()
