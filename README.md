# Declarative GitHub Setup Tool & Workflows

This `.github/` directory houses the centralized configuration, workflows, and tools for scaffolding and managing GitHub repositories declaratively.

Instead of writing custom bash scripts for every repository, you define your desired state in a single YAML configuration file (`github_configuration.yaml`) placed in the root of your project, and orchestrate its execution seamlessly via the `setup` tool using the GitHub API (`gh`).

## Prerequisites

1. **GitHub CLI (`gh`)**: Must be installed and authenticated (`gh auth login`).
   - [Installation Guide](https://cli.github.com/)
2. **Python 3**: The orchestration script is written in Python.

## Quick Start

1. Copy the example configuration to the root of your project:

   ```bash
   cp .github/github_configuration.example.yaml github_configuration.yaml
   ```

2. Modify `github_configuration.yaml` to suit your project's needs.

3. Ensure the setup script is executable:

   ```bash
   chmod +x .github/setup
   ```

4. Run the tool (it automatically loads `github_configuration.yaml` from your project root):

   ```bash
   ./.github/setup
   ```

## Configuration (`github_configuration.yaml`)

The `github_configuration.yaml` file is the heart of the scaffolding repository. It dictates everything from CI workflow features to repository rulesets.

The setup orchestration pipeline specifically looks at the `setup` block within `github_configuration.yaml`. The keys in this block determine where the payload is sent.

### Structure Overview

```yaml
description: "Repository Configuration"

integration:
  enabled: true
  # CI Workflow configuration goes here

setup:
  rulesets_branch_prefix_enforcement:
    {
      "name": "Branch Prefix Enforcement",
      "target": "branch",
      "enforcement": "active",
      "conditions": {
        "ref_name": {
          "include": ["~ALL"],
          "exclude": ["refs/heads/main"]
        }
      },
      "rules": [
        { "type": "creation" }
      ]
    }
```

### Key-to-Endpoint Inference

The script infers the API endpoint and HTTP method directly from the naming conventions of the keys within the `setup` object:

- **Keys starting with `rulesets_`**:
  - **Endpoint**: `repos/{owner}/{repo}/rulesets`
  - **Method**: `POST`
  - GitHub CLI automatically interpolates the `{owner}` and `{repo}` context for the current local directory.

## Command Line Options

While the tool is designed to run automatically by relying on `github_configuration.yaml`, it supports a few overrides for automation environments:

```text
Usage: ./setup [OPTIONS]

Options:
  -h, --help            Show this help message and exit
  -q, --quiet           Suppress all informational output (errors will still print)
  --docs                Display README.md using pydoc pager
  --force               Delete existing rulesets before creating new ones
  --update-repo         Replace current .github/ with scaffolding from github_scaffolding
```

If you encounter duplicate ruleset names, you can use the `--force` flag to automatically seek and destroy matching existing configurations prior to creating the new ones.
