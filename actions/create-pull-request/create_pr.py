#!/usr/bin/env python3
import json
import os
import subprocess
import sys

def parse_yaml(file_path):
    data = {}
    if not os.path.exists(file_path):
        return data
    current_section = None
    pr_section = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                if line_stripped == 'integration:':
                    current_section = 'integration'
                elif current_section == 'integration' and line.startswith('  pull_request:'):
                    pr_section = True
                elif pr_section and line.startswith('    '):
                    parts = line_stripped.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        data[key] = val
                elif not line.startswith('    ') and pr_section:
                    pr_section = False
    except Exception as e:
        print(f"::warning::Failed to parse YAML config {file_path}: {e}")
    return data

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--head', default='')
    parser.add_argument('--base', default='')
    parser.add_argument('--title', default='')
    parser.add_argument('--body', default='')
    parser.add_argument('--reviewer', default='')
    args = parser.parse_args()

    # 1. Resolve head branch
    head_branch = args.head.strip()
    if not head_branch:
        head_branch = os.environ.get('MERGED_BRANCH', '').strip()
    if not head_branch:
        github_ref = os.environ.get('GITHUB_REF', '')
        if github_ref.startswith('refs/heads/'):
            head_branch = github_ref[len('refs/heads/'):]
        else:
            head_branch = github_ref
    
    # 2. Resolve base, title, body from config if inputs are missing
    base_branch = args.base.strip()
    pr_title = args.title.strip()
    pr_body = args.body.strip()
    reviewer = args.reviewer.strip()
    
    config_yaml = "github_configuration.yaml"
    config_json = ".github/configuration.json"
    
    yaml_config = {}
    json_config = {}
    
    if os.path.exists(config_yaml):
        try:
            import yaml
            with open(config_yaml, 'r', encoding='utf-8') as f:
                ydata = yaml.safe_load(f) or {}
            yaml_config = ydata.get('integration', {}).get('pull_request', {})
        except ImportError:
            yaml_config = parse_yaml(config_yaml)
            
    if os.path.exists(config_json):
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                jdata = json.load(f) or {}
            json_config = jdata.get('integration', {}).get('pull_request', {})
        except Exception as e:
            print(f"::warning::Failed to parse JSON config {config_json}: {e}")
            
    # Apply configurations
    if not base_branch:
        base_branch = yaml_config.get('to_branch') or json_config.get('to_branch') or 'develop'
    if not pr_title:
        pr_title = yaml_config.get('title') or json_config.get('title') or f"Automated PR: {head_branch}"
    if not pr_body:
        pr_body = yaml_config.get('body') or json_config.get('body') or "Automated PR created by workflow."
        
    print(f"Checking for existing PR from {head_branch} to {base_branch}")
    
    # Check if PR exists via GitHub CLI (gh)
    try:
        cmd = [
            'gh', 'pr', 'list',
            '--base', base_branch,
            '--head', head_branch,
            '--state', 'open',
            '--json', 'number'
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pr_list = json.loads(res.stdout or '[]')
        existing_pr = pr_list[0].get('number') if pr_list else None
    except Exception as e:
        print(f"::warning::Failed to check existing PR via gh: {e}")
        existing_pr = None
        
    if existing_pr:
        print(f"PR already exists: #{existing_pr}. Updating it.")
        try:
            subprocess.run([
                'gh', 'pr', 'edit', str(existing_pr),
                '--title', pr_title,
                '--body', pr_body
            ], check=True)
        except Exception as e:
            print(f"::error::Failed to edit PR: {e}")
            sys.exit(1)
    else:
        print("Creating new PR...")
        try:
            create_cmd = [
                'gh', 'pr', 'create',
                '--base', base_branch,
                '--head', head_branch,
                '--title', pr_title,
                '--body', pr_body
            ]
            if reviewer:
                create_cmd.extend(['--reviewer', reviewer])
                
            subprocess.run(create_cmd, check=True)
        except Exception as e:
            print(f"::error::Failed to create PR: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
