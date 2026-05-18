#!/usr/bin/env python3
import datetime
import json
import os
import re
import subprocess
import sys

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefixes', default='')
    parser.add_argument('--prefixes-env', default='')
    parser.add_argument('--target-branch-prefix', default='')
    args = parser.parse_args()
    
    # 1. Load config
    config_file = ".github/configuration.json"
    conf_target_prefix = "nightly"
    append_date = True
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            integration = data.get('integration', {})
            conf_target_prefix = integration.get('output_branch_prefix', 'nightly')
            app_date = integration.get('output_branch_append_date')
            if app_date is not None:
                append_date = bool(app_date)
        except Exception as e:
            print(f"::warning::Failed to parse JSON config: {e}")
            
    # 2. Determine Prefix List
    prefix_list = args.prefixes.strip()
    if not prefix_list:
        prefix_list = args.prefixes_env.strip()
        
    if not prefix_list:
        print("Error: No prefixes provided and PREFIXES environment variable is empty.")
        sys.exit(1)
        
    # 3. Determine Target Prefix
    target_prefix = args.target_branch_prefix.strip()
    if not target_prefix:
        target_prefix = conf_target_prefix
        
    # 4. Build Final Branch Name
    date_str = datetime.datetime.utcnow().strftime('%Y%m%d')
    if append_date:
        final_branch = f"{target_prefix}/{date_str}"
    else:
        final_branch = target_prefix
        
    print(f"Merging branches matching prefixes: {prefix_list}")
    print(f"Target branch: {final_branch}")
    
    try:
        # Create a temporary working branch
        subprocess.run(['git', 'checkout', '-b', 'merge-tmp'], check=True)
        
        # Discover remote branches
        res = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True, check=True)
        remote_branches = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        
        # Compile a regex to match prefixes
        pattern = f"^origin/({prefix_list})"
        rx = re.compile(pattern)
        
        matched_branches = []
        for rb in remote_branches:
            rb_clean = rb.replace('*', '').strip()
            match = rx.search(rb_clean)
            if match:
                if rb_clean.startswith('origin/'):
                    matched_branches.append(rb_clean[7:])
                else:
                    matched_branches.append(rb_clean)
                    
        if not matched_branches:
            print("No branches found matching prefixes.")
        else:
            for branch in matched_branches:
                print("========================================")
                print(f"Merging {branch}...")
                print("========================================")
                res = subprocess.run(['git', 'merge', f"origin/{branch}"])
                if res.returncode != 0:
                    print(f"Merge conflict on {branch}")
                    sys.exit(1)
                    
        # Rename to final target
        subprocess.run(['git', 'branch', '-M', final_branch], check=True)
        
        # Outputs for GitHub Actions
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a', encoding='utf-8') as f:
                f.write(f"date={date_str}\n")
                f.write(f"branch_name={final_branch}\n")
        else:
            print(f"OUTPUT: date={date_str}")
            print(f"OUTPUT: branch_name={final_branch}")
            
        github_env = os.environ.get('GITHUB_ENV')
        if github_env:
            with open(github_env, 'a', encoding='utf-8') as f:
                f.write(f"DATE={date_str}\n")
                f.write(f"MERGED_BRANCH={final_branch}\n")
        else:
            print(f"ENV: DATE={date_str}")
            print(f"ENV: MERGED_BRANCH={final_branch}")
            
    except Exception as e:
        print(f"::error::Git operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
