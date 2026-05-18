#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def main():
    has_error = False
    for root, dirs, files in os.walk('.'):
        for exclude in ['.venv', 'node_modules', 'vendor', '.git']:
            if exclude in dirs:
                dirs.remove(exclude)
                
        if 'requirements.txt' in files:
            req_path = os.path.join(root, 'requirements.txt')
            dir_path = os.path.abspath(root)
            print(f"Python project detected at {req_path}")
            
            venv_dir = os.path.join(dir_path, '.venv')
            if os.path.exists(venv_dir):
                try:
                    shutil.rmtree(venv_dir)
                except Exception as e:
                    print(f"::warning::Failed to remove existing .venv: {e}")
                
            try:
                # Create virtual environment
                res = subprocess.run([sys.executable, '-m', 'venv', '.venv'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::Failed to create virtual environment in {dir_path}")
                    has_error = True
                    continue
                    
                # Setup paths for python/pip in venv
                if os.name == 'nt':
                    venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
                    venv_pip = os.path.join(venv_dir, 'Scripts', 'pip.exe')
                    venv_pytest = os.path.join(venv_dir, 'Scripts', 'pytest.exe')
                else:
                    venv_python = os.path.join(venv_dir, 'bin', 'python')
                    venv_pip = os.path.join(venv_dir, 'bin', 'pip')
                    venv_pytest = os.path.join(venv_dir, 'bin', 'pytest')
                    
                # Upgrade pip
                res = subprocess.run([venv_pip, 'install', '--upgrade', 'pip'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::Failed to upgrade pip in {dir_path}")
                    has_error = True
                    continue
                    
                # Install requirements
                res = subprocess.run([venv_pip, 'install', '-r', 'requirements.txt'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::Failed to install requirements in {dir_path}")
                    has_error = True
                    continue
                    
                # Run pytest
                pytest_cmd = [venv_pytest] if os.path.exists(venv_pytest) else [venv_python, '-m', 'pytest']
                res = subprocess.run(pytest_cmd, cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::pytest failed in {dir_path}")
                    has_error = True
            except Exception as e:
                print(f"::error::Failed to validate Python project in {dir_path}: {e}")
                has_error = True
                
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
