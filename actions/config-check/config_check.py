#!/usr/bin/env python3
import os
import sys
import json
import subprocess

def main():
    has_error = False
    
    # 1. Yamllint for .github/workflows
    if os.path.exists(".github/workflows"):
        print("Linting workflows in .github/workflows...")
        try:
            res = subprocess.run([
                'yamllint', 
                '-d', 
                '{extends: default, rules: {line-length: disable, truthy: disable}}', 
                '.github/workflows'
            ])
            if res.returncode != 0:
                print("::error::yamllint failed for .github/workflows")
                has_error = True
        except Exception as e:
            print(f"::error::Failed to run yamllint: {e}")
            has_error = True
            
    # 2. JSON validation for .github/configuration.json
    config_json = ".github/configuration.json"
    if os.path.exists(config_json):
        print(f"Validating JSON configuration: {config_json}")
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"Successfully validated JSON: {config_json}")
        except Exception as e:
            print(f"::error::JSON validation failed for {config_json}: {e}")
            has_error = True
            
    # 3. YAML validation for github_configuration.yaml
    config_yaml = "github_configuration.yaml"
    if os.path.exists(config_yaml):
        print(f"Validating YAML configuration: {config_yaml}")
        try:
            try:
                import yaml
                with open(config_yaml, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                print(f"Successfully validated YAML using pyyaml: {config_yaml}")
            except ImportError:
                # Fallback to yq command
                res = subprocess.run(['yq', 'eval', '.', config_yaml], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    print(f"::error::YAML validation failed for {config_yaml}: {res.stderr.decode('utf-8')}")
                    has_error = True
                else:
                    print(f"Successfully validated YAML using yq fallback: {config_yaml}")
        except Exception as e:
            print(f"::error::YAML validation failed for {config_yaml}: {e}")
            has_error = True
            
    if has_error:
        sys.exit(1)

if __name__ == '__main__':
    main()
