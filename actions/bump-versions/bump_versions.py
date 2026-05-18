#!/usr/bin/env python3
from datetime import datetime
import json
import os
import re
import subprocess
import sys

def parse_yaml_config(file_path):
    """
    Lightweight, zero-dependency YAML parser designed to extract the list of
    version files from the 'versioning.files' block of the configuration file.
    """
    if not os.path.exists(file_path):
        return []
    
    files = []
    in_versioning_section = False
    in_files_section = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Detect top-level key structure
            if stripped.startswith('versioning:'):
                in_versioning_section = True
                in_files_section = False
                continue
                
            if in_versioning_section:
                # If we hit another top-level key (starts with letter without indentation),
                # we exit the versioning section.
                if line and line[0].isalpha() and not stripped.startswith('versioning:'):
                    in_versioning_section = False
                    in_files_section = False
                    continue
                
                if stripped.startswith('files:'):
                    in_files_section = True
                    continue
                    
                if in_files_section:
                    if stripped.startswith('-'):
                        file_item = stripped[1:].strip()
                        # Strip trailing comments
                        if '#' in file_item:
                            file_item = file_item.split('#', 1)[0].strip()
                        # Clean quotes
                        file_item = file_item.strip('"\'')
                        if file_item:
                            files.append(file_item)
                    elif line and not line.startswith(' ') and not line.startswith('\t'):
                        in_versioning_section = False
                        in_files_section = False
    return files

def detect_json_indent(content):
    """
    Detects the indentation spacing of a JSON string.
    """
    for line in content.splitlines():
        if line.startswith(' ') and not line.startswith(' }') and not line.startswith(' ]'):
            return len(line) - len(line.lstrip(' '))
        if line.startswith('\t'):
            return '\t'
    return 2

def parse_and_bump_version(old_version, date_str):
    """
    Parses a semantic version string (e.g. 1.2.3, 1.2.3-20260511, 1.2.3+1)
    and returns a new version with the patch number incremented and the
    nightly date appended (e.g. 1.2.4-20260518).
    """
    main_part = old_version
    # Strip build metadata starting with '+' or pre-release suffixes starting with '-'
    if '+' in main_part:
        main_part = main_part.split('+', 1)[0]
    if '-' in main_part:
        main_part = main_part.split('-', 1)[0]
        
    parts = main_part.split('.')
    if len(parts) >= 3:
        major, minor, patch = parts[0], parts[1], parts[2]
        try:
            new_patch = int(patch) + 1
            return f"{major}.{minor}.{new_patch}-{date_str}"
        except ValueError:
            pass
            
    # Fallback to incrementing the last integer in the version string
    match = re.search(r'(\d+)(?!.*\d)', main_part)
    if match:
        num = int(match.group(1))
        start, end = match.span()
        new_main = main_part[:start] + str(num + 1) + main_part[end:]
        return f"{new_main}-{date_str}"
        
    return f"{old_version}-bumped-{date_str}"

def bump_json(file_path, date_str, dry_run=False):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    indent = detect_json_indent(content)
    data = json.loads(content)
    if 'version' in data:
        old_version = data['version']
        new_version = parse_and_bump_version(old_version, date_str)
        
        if not dry_run:
            data['version'] = new_version
            updated_content = json.dumps(data, indent=indent, ensure_ascii=False)
            if content.endswith('\n') and not updated_content.endswith('\n'):
                updated_content += '\n'
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        return old_version, new_version
    else:
        raise ValueError("Key 'version' not found in JSON file")

def bump_toml(file_path, date_str, dry_run=False):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = r'^(\s*version\s*=\s*["\'])([^"\']+)(["\']\s*.*)$'
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        old_version = match.group(2)
        new_version = parse_and_bump_version(old_version, date_str)
        
        if not dry_run:
            updated_content, count = re.subn(pattern, lambda m: m.group(1) + new_version + m.group(3), content, count=1, flags=re.MULTILINE)
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
        return old_version, new_version
    raise ValueError("Version string not found in TOML file")

def bump_yaml(file_path, date_str, dry_run=False):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = r'^(\s*version\s*:\s*["\']?)([^"\’\s\n]+)(["\']?\s*.*)$'
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        old_version = match.group(2)
        new_version = parse_and_bump_version(old_version, date_str)
        
        if not dry_run:
            updated_content, count = re.subn(pattern, lambda m: m.group(1) + new_version + m.group(3), content, count=1, flags=re.MULTILINE)
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
        return old_version, new_version
    raise ValueError("Version string not found in YAML file")

def bump_text(file_path, date_str, dry_run=False):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.strip().splitlines()
    if len(lines) <= 1 or file_path.endswith('VERSION'):
        old_version = content.strip()
        new_version = parse_and_bump_version(old_version, date_str)
        
        if not dry_run:
            suffix = '\n' if content.endswith('\n') else ''
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_version + suffix)
        return old_version, new_version
    else:
        # Match standard version X.Y.Z
        pattern = r'\b(\d+\.\d+\.\d+(?:-[^\s\n"\'#]+)?)\b'
        match = re.search(pattern, content)
        if match:
            old_version = match.group(1)
            new_version = parse_and_bump_version(old_version, date_str)
            
            if not dry_run:
                updated_content = content[:match.start()] + new_version + content[match.end():]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
            return old_version, new_version
        raise ValueError("Semantic version pattern not found in text file")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bump versions in various files.")
    parser.add_argument('files', nargs='*', help='Explicit list of files to bump.')
    parser.add_argument('--dry-run', action='store_true', help='Simulate the bumping process without writing changes to disk or committing.')
    parser.add_argument('--no-commit', action='store_true', help='Write changes to disk but do not stage or commit them in git.')
    
    args = parser.parse_args()
    
    if args.files:
        files = args.files
    else:
        # Try loading from github_configuration.yaml
        files = parse_yaml_config('github_configuration.yaml')
        if not files:
            print("github_configuration.yaml not found or empty, trying github_configuration.example.yaml...")
            files = parse_yaml_config('github_configuration.example.yaml')
            
    if not files:
        print("No version files specified or found in configuration.")
        sys.exit(0)
        
    date_str = datetime.now().strftime('%Y%m%d')
    bumped_files = []
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"Skipping: {file_path} (File not found)")
            continue
            
        print(f"Processing {file_path}...")
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.json':
                old, new = bump_json(file_path, date_str, dry_run=args.dry_run)
            elif ext == '.toml':
                old, new = bump_toml(file_path, date_str, dry_run=args.dry_run)
            elif ext in ('.yaml', '.yml'):
                old, new = bump_yaml(file_path, date_str, dry_run=args.dry_run)
            else:
                # Text, Markdown or raw VERSION file
                old, new = bump_text(file_path, date_str, dry_run=args.dry_run)
                
            prefix = "[DRY RUN] Would bump" if args.dry_run else "Successfully bumped"
            print(f"  {prefix} {old} -> {new}")
            bumped_files.append(file_path)
        except Exception as e:
            print(f"  Failed to bump {file_path}: {e}")
            
    if bumped_files and not args.dry_run and not args.no_commit:
        print("\nStaging and committing bumped version files...")
        try:
            # Git config
            subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            
            # Git add individual files
            for file_path in bumped_files:
                subprocess.run(["git", "add", file_path], check=True)
                
            # Git commit
            subprocess.run(["git", "commit", "-m", "Bump versions for nightly build"], check=True)
            print("Successfully committed version bumps!")
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            sys.exit(1)
    else:
        if args.dry_run:
            print("\nDry run completed. No changes made.")
        elif args.no_commit:
            print("\nChanges written to disk. Skipping git stage and commit as requested.")
        else:
            print("\nNo files were successfully bumped.")

if __name__ == '__main__':
    main()
