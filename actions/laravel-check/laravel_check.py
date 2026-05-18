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
                
        if 'composer.json' in files:
            comp_path = os.path.join(root, 'composer.json')
            dir_path = os.path.abspath(root)
            print(f"Laravel/PHP project detected at {comp_path}")
            
            try:
                # 1. composer validate
                res = subprocess.run(['composer', 'validate', '--no-check-all'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::composer validate failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 2. composer install
                res = subprocess.run([
                    'composer', 'install', '--no-progress', 
                    '--prefer-dist', '--optimize-autoloader'
                ], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::composer install failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 3. php artisan --version
                res = subprocess.run(['php', 'artisan', '--version'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::php artisan --version failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 4. php artisan config:clear
                res = subprocess.run(['php', 'artisan', 'config:clear'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::artisan config:clear failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 5. php artisan cache:clear
                res = subprocess.run(['php', 'artisan', 'cache:clear'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::artisan cache:clear failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 6. php artisan migrate --env=testing --force
                res = subprocess.run([
                    'php', 'artisan', 'migrate', 
                    '--env=testing', '--force'
                ], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::artisan migrate failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 7. php artisan route:list
                res = subprocess.run(['php', 'artisan', 'route:list'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::artisan route:list failed in {dir_path}")
                    has_error = True
                    continue
                    
                # 8. php artisan test --env=testing
                res = subprocess.run(['php', 'artisan', 'test', '--env=testing'], cwd=dir_path)
                if res.returncode != 0:
                    print(f"::error::artisan test failed in {dir_path}")
                    has_error = True
            except Exception as e:
                print(f"::error::Failed to validate Laravel/PHP project in {dir_path}: {e}")
                has_error = True
                
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
