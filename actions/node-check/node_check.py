#!/usr/bin/env python3
import os
import sys
import json
import subprocess

def main():
    has_error = False
    for root, dirs, files in os.walk('.'):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
            
        if 'package.json' in files:
            pkg_path = os.path.join(root, 'package.json')
            if 'hello-laravel/backend/package.json' in pkg_path:
                print("Skipping Laravel backend npm build...")
                continue
                
            print(f"Node project detected at {pkg_path}")
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)
            except Exception as e:
                print(f"::error::Failed to read/parse {pkg_path}: {e}")
                has_error = True
                continue
                
            scripts = pkg_data.get('scripts', {})
            if 'build' in scripts:
                dir_path = os.path.abspath(root)
                has_lock = os.path.exists(os.path.join(root, 'package-lock.json'))
                install_cmd = ['npm', 'ci'] if has_lock else ['npm', 'install']
                
                try:
                    res = subprocess.run(install_cmd, cwd=dir_path)
                    if res.returncode != 0:
                        print(f"::error::npm install failed in {dir_path}")
                        has_error = True
                        continue
                        
                    res = subprocess.run(['npm', 'run', 'build'], cwd=dir_path)
                    if res.returncode != 0:
                        print(f"::error::npm run build failed in {dir_path}")
                        has_error = True
                except Exception as e:
                    print(f"::error::Failed to run Node commands in {dir_path}: {e}")
                    has_error = True
            else:
                print("No build script defined, skipping")
                
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
