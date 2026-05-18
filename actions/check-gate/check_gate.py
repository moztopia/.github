#!/usr/bin/env python3
import json
import os

def parse_yaml_integration_enabled(file_path):
    """
    Parses a YAML file and returns the value of integration.enabled.
    Defaults to True if not explicitly specified.
    """
    if not os.path.exists(file_path):
        return None
    
    in_integration = False
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if stripped.startswith('integration:'):
                in_integration = True
                continue
                
            if in_integration:
                # If we encounter another top-level key, we exit integration section
                if line and line[0].isalpha() and not stripped.startswith('integration:'):
                    in_integration = False
                    continue
                
                # Check for enabled: true/false
                if stripped.startswith('enabled:'):
                    value = stripped.split(':', 1)[1].strip()
                    # Strip comments
                    if '#' in value:
                        value = value.split('#', 1)[0].strip()
                    return value.lower() == 'true'
    return True

def parse_json_integration_enabled(file_path):
    """
    Parses a JSON file and returns the value of integration.enabled.
    Defaults to True if not explicitly specified.
    """
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        integration = data.get('integration')
        if isinstance(integration, dict):
            enabled = integration.get('enabled')
            if enabled is not None:
                return bool(enabled)
    except Exception:
        pass
    return True

def main():
    enabled = True
    
    if os.path.exists("github_configuration.yaml"):
        val = parse_yaml_integration_enabled("github_configuration.yaml")
        if val is not None:
            enabled = val
    elif os.path.exists(".github/configuration.json"):
        val = parse_json_integration_enabled(".github/configuration.json")
        if val is not None:
            enabled = val
            
    enabled_str = "true" if enabled else "false"
    print(f"Gate status: {enabled_str}")
    
    # Write to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"enabled={enabled_str}\n")
    else:
        print(f"enabled={enabled_str}")

if __name__ == '__main__':
    main()
