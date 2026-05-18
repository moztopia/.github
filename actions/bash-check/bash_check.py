#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    has_error = False
    for root, dirs, files in os.walk('.'):
        for exclude in ['node_modules', '.venv', 'vendor', '.git']:
            if exclude in dirs:
                dirs.remove(exclude)
                
        for file in files:
            if file.endswith('.sh'):
                script_path = os.path.join(root, file)
                print(f"Linting bash script {script_path}")
                try:
                    res = subprocess.run(['bash', '-n', script_path])
                    if res.returncode != 0:
                        print(f"::error::Linting failed for {script_path}")
                        has_error = True
                except Exception as e:
                    print(f"::error::Failed to run bash -n on {script_path}: {e}")
                    has_error = True
                    
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
