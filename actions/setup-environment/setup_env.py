#!/usr/bin/env python3
import json
import os
import sys

def parse_yaml_config(file_path):
    """
    Parses the github_configuration.yaml file and extracts integration and code_checks.
    """
    config = {
        'target_branch': 'develop',
        'branch_prefixes': [],
        'allow_manual_run': True,
        'code_checks': {
            'node': True,
            'python': True,
            'laravel': True,
            'rust': True,
            'dart': True,
            'makefile': True,
            'bash': True,
            'markdown': True,
            'config': True
        }
    }
    
    if not os.path.exists(file_path):
        return config
        
    in_integration = False
    in_prefixes = False
    in_code_checks = False
    current_check = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            # Track top-level blocks
            if stripped.startswith('integration:'):
                in_integration = True
                in_prefixes = False
                in_code_checks = False
                continue
            elif stripped.startswith('code_checks:'):
                in_integration = False
                in_prefixes = False
                in_code_checks = True
                continue
            elif line[0].isalpha():
                # Any other top-level block
                in_integration = False
                in_prefixes = False
                in_code_checks = False
                continue
                
            # Parse inside integration
            if in_integration:
                if stripped.startswith('target_branch:'):
                    val = stripped.split(':', 1)[1].strip().split('#', 1)[0].strip().strip('"\'')
                    if val:
                        config['target_branch'] = val
                elif stripped.startswith('allow_manual_run:'):
                    val = stripped.split(':', 1)[1].strip().split('#', 1)[0].strip().lower()
                    config['allow_manual_run'] = (val == 'true')
                elif stripped.startswith('branch_prefixes:'):
                    in_prefixes = True
                    continue
                
                if in_prefixes:
                    if stripped.startswith('-'):
                        prefix = stripped[1:].strip().split('#', 1)[0].strip().strip('"\'')
                        if prefix:
                            config['branch_prefixes'].append(prefix)
                    elif not line.startswith(' ') and not line.startswith('\t'):
                        in_prefixes = False
            
            # Parse inside code_checks
            elif in_code_checks:
                # Detect second-level check block, e.g., 'node:'
                indent = len(line) - len(line.lstrip())
                if indent > 0 and stripped.endswith(':'):
                    check_name = stripped[:-1].strip()
                    if check_name in config['code_checks']:
                        current_check = check_name
                    else:
                        current_check = None
                elif current_check and stripped.startswith('enabled:'):
                    val = stripped.split(':', 1)[1].strip().split('#', 1)[0].strip().lower()
                    config['code_checks'][current_check] = (val == 'true')
                elif not line.startswith(' ') and not line.startswith('\t'):
                    in_code_checks = False
                    current_check = None
                    
    return config

def parse_json_config(file_path):
    config = {
        'target_branch': 'develop',
        'branch_prefixes': [],
        'allow_manual_run': True,
        'code_checks': {
            'node': True,
            'python': True,
            'laravel': True,
            'rust': True,
            'dart': True,
            'makefile': True,
            'bash': True,
            'markdown': True,
            'config': True
        }
    }
    
    if not os.path.exists(file_path):
        return config
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        integration = data.get('integration', {})
        if isinstance(integration, dict):
            config['target_branch'] = integration.get('target_branch', 'develop')
            prefixes = integration.get('branch_prefixes', [])
            if isinstance(prefixes, list):
                config['branch_prefixes'] = [str(p) for p in prefixes]
            allow_manual = integration.get('allow_manual_run')
            if allow_manual is not None:
                config['allow_manual_run'] = bool(allow_manual)
                
        code_checks = data.get('code_checks', {})
        if isinstance(code_checks, dict):
            for check, check_val in code_checks.items():
                if check in config['code_checks'] and isinstance(check_val, dict):
                    enabled = check_val.get('enabled')
                    if enabled is not None:
                        config['code_checks'][check] = bool(enabled)
    except Exception as e:
        print(f"::warning::Failed to parse JSON config: {e}")
        
    return config

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--event-name', default='', help='GitHub Event Name')
    args = parser.parse_args()
    
    config = None
    if os.path.exists("github_configuration.yaml"):
        print("Loading configuration from github_configuration.yaml")
        config = parse_yaml_config("github_configuration.yaml")
    elif os.path.exists(".github/configuration.json"):
        print("Loading configuration from .github/configuration.json")
        config = parse_json_config(".github/configuration.json")
    else:
        print("::warning::No configuration file found. Using defaults.")
        config = {
            'target_branch': 'develop',
            'branch_prefixes': ['feat/', 'chore/', 'bug/', 'docs/', 'test/'],
            'allow_manual_run': True,
            'code_checks': {k: True for k in ['node', 'python', 'laravel', 'rust', 'dart', 'makefile', 'bash', 'markdown', 'config']}
        }
        
    # Match exact bash formatting for prefixes (joined by '|')
    prefixes_str = '|'.join(config['branch_prefixes']) if config['branch_prefixes'] else "feat|fix|chore"
    
    # Enforce manual run restriction
    if args.event_name == 'workflow_dispatch' and not config['allow_manual_run']:
        print("::error::Manual runs (workflow_dispatch) are disabled in configuration.")
        sys.exit(1)
        
    # Write to GITHUB_ENV
    github_env = os.environ.get('GITHUB_ENV')
    def write_env(key, val):
        val_str = str(val).lower() if isinstance(val, bool) else str(val)
        if github_env:
            with open(github_env, 'a', encoding='utf-8') as f:
                f.write(f"{key}={val_str}\n")
        else:
            print(f"ENV: {key}={val_str}")
            
    write_env("TARGET_BRANCH", config['target_branch'])
    write_env("PREFIXES", prefixes_str)
    
    for check, enabled in config['code_checks'].items():
        write_env(f"CHECK_{check.upper()}", enabled)
        
    # Write output target_branch to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"target_branch={config['target_branch']}\n")
    else:
        print(f"OUTPUT: target_branch={config['target_branch']}")

if __name__ == '__main__':
    main()
