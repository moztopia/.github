#!/usr/bin/env python3
import datetime
import json
import os
import re
import subprocess
import sys

def run_cmd(cmd, check=True, capture_output=True, text=True):
    """
    Executes a shell command as a subprocess and logs the invocation.
    """
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, check=check, capture_output=capture_output, text=text)
    return res

def parse_yaml_config(file_path):
    """
    Parses the github_configuration.yaml file and extracts integration and code_checks.
    """
    config = {
        'target_branch': 'develop',
        'code_checks': {}
    }
    if not os.path.exists(file_path):
        return config
    
    in_integration = False
    in_code_checks = False
    current_check = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if stripped.startswith('integration:'):
                in_integration = True
                in_code_checks = False
                continue
            elif stripped.startswith('code_checks:'):
                in_integration = False
                in_code_checks = True
                continue
            elif line[0].isalpha():
                in_integration = False
                in_code_checks = False
                continue
                
            if in_integration:
                if stripped.startswith('target_branch:'):
                    val = stripped.split(':', 1)[1].strip().split('#', 1)[0].strip().strip('"\'')
                    if val:
                        config['target_branch'] = val
            elif in_code_checks:
                indent = len(line) - len(line.lstrip())
                if indent > 0 and stripped.endswith(':'):
                    check_name = stripped[:-1].strip()
                    config['code_checks'][check_name] = True  # Default to True
                    current_check = check_name
                elif current_check and stripped.startswith('enabled:'):
                    val = stripped.split(':', 1)[1].strip().split('#', 1)[0].strip().lower()
                    config['code_checks'][current_check] = (val == 'true')
                elif not line.startswith(' ') and not line.startswith('\t'):
                    in_code_checks = False
                    current_check = None
                    
    return config

def parse_json_config(file_path):
    """
    Parses a JSON configuration file and extracts branch integration target
    and the status of active validation checkers.
    """
    config = {
        'target_branch': 'develop',
        'code_checks': {}
    }
    if not os.path.exists(file_path):
        return config
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        integration = data.get('integration', {})
        if isinstance(integration, dict):
            config['target_branch'] = integration.get('target_branch', 'develop')
        code_checks = data.get('code_checks', {})
        if isinstance(code_checks, dict):
            for check, check_val in code_checks.items():
                if isinstance(check_val, dict):
                    enabled = check_val.get('enabled')
                    if enabled is not None:
                        config['code_checks'][check] = bool(enabled)
    except Exception as e:
        print(f"Warning: Failed to parse JSON config: {e}")
    return config

def get_config():
    """
    Finds and parses the first available configuration file in YAML or JSON format,
    falling back to standard default values if none are found.
    """
    if os.path.exists("github_configuration.yaml"):
        return parse_yaml_config("github_configuration.yaml")
    elif os.path.exists(".github/configuration.json"):
        return parse_json_config(".github/configuration.json")
    return {
        'target_branch': 'develop',
        'code_checks': {k: True for k in ['node', 'python', 'laravel', 'rust', 'dart', 'makefile', 'bash', 'markdown', 'config']}
    }

def main():
    """
    Orchestrates the build-bot integration flow: retrieves remote branches,
    resolves the daily sequential branch name, performs speculative merges,
    runs polyglot validation checks on clean branches, and pushes the final branch.
    """
    config = get_config()
    target_branch = config['target_branch']
    print(f"Base target branch: {target_branch}")
    
    # Ensure remote changes are fully fetched
    print("Fetching remote updates...")
    run_cmd(['git', 'fetch', '--all', '--prune'], check=False)
    
    # Discover remote branches
    res = run_cmd(['git', 'branch', '-r'])
    remote_branches = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.replace('*', '').strip()
        if line.startswith('origin/build/') and not line.startswith('origin/build/bot-'):
            remote_branches.append(line[7:])
            
    remote_branches.sort()
    
    if not remote_branches:
        print("No remote branches matching 'build/*' (excluding 'build/bot-*') were found.")
        sys.exit(0)
        
    print(f"Found candidate remote branches: {', '.join(remote_branches)}")
    
    # Determine the sequential build branch name
    now = datetime.datetime.now()
    today_str = now.strftime('%Y%m%d')
    seq_pattern = re.compile(rf"^origin/build/bot-{today_str}-(\d{{3}})$")
    
    existing_nums = []
    for line in res.stdout.splitlines():
        line = line.strip().replace('*', '').strip()
        match = seq_pattern.match(line)
        if match:
            existing_nums.append(int(match.group(1)))
            
    next_seq = 1 if not existing_nums else max(existing_nums) + 1
    seq_str = f"{next_seq:03d}"
    new_branch_name = f"build/bot-{today_str}-{seq_str}"
    
    print(f"Determined target build branch: {new_branch_name}")
    
    # Checkout base target branch
    print(f"Preparing base branch: {target_branch}")
    try:
        run_cmd(['git', 'checkout', target_branch])
        run_cmd(['git', 'reset', '--hard', f"origin/{target_branch}"], check=False)
    except Exception as e:
        print(f"Error checking out {target_branch}: {e}")
        sys.exit(1)
        
    # Create the build branch
    try:
        run_cmd(['git', 'checkout', '-b', new_branch_name])
    except Exception as e:
        print(f"Error creating new branch {new_branch_name}: {e}")
        sys.exit(1)
        
    integrated_branches = []
    failed_branches = []
    
    for branch in remote_branches:
        print(f"\n========================================")
        print(f"Speculatively merging: {branch}")
        print(f"========================================")
        
        # Savepoint SHA before merge
        res_sha = run_cmd(['git', 'rev-parse', 'HEAD'])
        savepoint_sha = res_sha.stdout.strip()
        
        # Merge candidate branch
        merge_res = run_cmd(['git', 'merge', f"origin/{branch}"], check=False)
        
        if merge_res.returncode != 0:
            print(f"❌ Merge conflict while merging {branch}. Discarding integration.")
            run_cmd(['git', 'merge', '--abort'], check=False)
            run_cmd(['git', 'reset', '--hard', savepoint_sha], check=False)
            failed_branches.append((branch, "Merge Conflict"))
            continue
            
        # Merge succeeded, run validations
        print("Merge succeeded. Running validation checkers...")
        validation_failed = False
        failed_check_name = ""
        
        checkers = ['node', 'python', 'laravel', 'rust', 'dart', 'makefile', 'bash', 'markdown', 'config']
        for check in checkers:
            enabled = config['code_checks'].get(check, True)
            if not enabled:
                print(f"ℹ️ Checker '{check}' is disabled in configuration. Skipping.")
                continue
                
            script_path = f"actions/{check}-check/{check}_check.py"
            if not os.path.exists(script_path):
                print(f"⚠️ Checker script not found: {script_path}. Skipping.")
                continue
                
            print(f"Running '{check}' validation...")
            check_res = run_cmd(['python3', script_path], check=False)
            
            if check_res.returncode != 0:
                print(f"❌ Validation '{check}' failed for branch {branch}!")
                validation_failed = True
                failed_check_name = check
                break
                
        if validation_failed:
            print(f"Discarding integration of {branch} due to validation failures.")
            run_cmd(['git', 'reset', '--hard', savepoint_sha], check=False)
            run_cmd(['git', 'clean', '-fd'], check=False)
            failed_branches.append((branch, f"Failed validation: {failed_check_name}"))
        else:
            print(f"✅ Successfully integrated {branch} into the build branch!")
            integrated_branches.append(branch)
            
    print(f"\n========================================")
    print(f"Build Bot Summary:")
    print(f"Successfully integrated ({len(integrated_branches)}): {', '.join(integrated_branches) if integrated_branches else 'None'}")
    print(f"Failed / Excluded ({len(failed_branches)}):")
    for fb, reason in failed_branches:
        print(f"  - {fb} ({reason})")
    print(f"========================================")
    
    # Push branch if any integrations succeeded
    if integrated_branches:
        print(f"Pushing build bot branch to remote: {new_branch_name}")
        push_res = run_cmd(['git', 'push', 'origin', new_branch_name], check=False)
        if push_res.returncode != 0:
            print("::error::Failed to push build-bot branch to origin.")
            sys.exit(1)
        print(f"Successfully created and pushed build branch: {new_branch_name}")
    else:
        print("No branches were successfully integrated. Skipping remote branch push.")
        # Switch back to base branch and delete the local bot branch
        run_cmd(['git', 'checkout', target_branch], check=False)
        run_cmd(['git', 'branch', '-D', new_branch_name], check=False)

if __name__ == '__main__':
    main()
