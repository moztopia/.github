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
                
        if 'pubspec.yaml' in files:
            pubspec_path = os.path.join(root, 'pubspec.yaml')
            dir_path = os.path.abspath(root)
            print(f"Dart/Flutter project detected at {pubspec_path}")
            
            try:
                res = subprocess.run(['dart', 'pub', 'get'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::dart pub get failed in {dir_path}")
                    has_error = True
                    continue
                    
                res = subprocess.run(['dart', 'test'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::dart test failed in {dir_path}")
                    has_error = True
            except Exception as e:
                print(f"::error::Failed to validate Dart/Flutter project in {dir_path}: {e}")
                has_error = True
                
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
