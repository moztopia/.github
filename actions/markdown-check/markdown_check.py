#!/usr/bin/env python3
import os
import sys

def main():
    has_error = False
    for root, dirs, files in os.walk('.'):
        for exclude in ['node_modules', '.venv', '.pytest_cache', 'vendor', '.git']:
            if exclude in dirs:
                dirs.remove(exclude)
                
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                print(f"Checking markdown file {md_path}")
                try:
                    has_content = False
                    with open(md_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                has_content = True
                                break
                    if not has_content:
                        print(f"::error::Markdown file is empty: {md_path}")
                        has_error = True
                except Exception as e:
                    print(f"::error::Failed to check markdown file {md_path}: {e}")
                    has_error = True
                    
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
