# 🌙 Automated Integration & Validation

Welcome to the automated heart of our repository's cross-component integration. This directory contains the **Automated Integration** engine, a comprehensive workflow designed to ensure seamless compatibility across our polyglot codebase.

---

## 🛠️ Workflow Overview

**File:** [`automated_integration.yaml`](./automated_integration.yaml)  
**Triggers:** Scheduled (see YAML) or Manual Dispatch via `workflow_dispatch`.

The Automated Integration is our comprehensive validation engine. It performs a "Deep Merge" of all active feature branches to detect integration conflicts and cross-project regressions before they reach the main development branches.

**File:** [`integration_robot.yaml`](./integration_robot.yaml)  
**Triggers:** Push to feature prefixes, Scheduled (Nightly), or Manual.

The Integration Robot is a hardened, "not all or nothing" variant of our integration engine. It prioritizes stability by individually validating each candidate branch. If a specific branch fails tests or has conflicts, it is automatically excluded from the nightly build, ensuring the resulting `nightly/` branch remains in a deployable state.

**File:** [`build-bot.yaml`](./build-bot.yaml)  
**Triggers:** Scheduled (Daily) or Manual Dispatch via `workflow_dispatch`.

The Build Bot is a speculatively automated integration system. It queries the remote repository for all matching `build/*` branches (excluding circular `build/bot-*` branches) and speculatively merges them one-by-one. Each branch that merges cleanly and passes all enabled polyglot validation checks is incorporated; any branch that fails or conflicts is seamlessly rolled back and left out of the final daily build branch (`build/bot-YYYYMMDD-###`).

### 🔄 The Process

1. **Environment Setup:** Uses a standardized [setup action](./.github/actions/setup-environment) to configure Git and discover active branch prefixes from [`.github/configuration.json`](../configuration.json).
2. **Sequential Merge:** Uses the [git-merge-prefixes action](./.github/actions/git-merge-prefixes) to systematically merge matching remote branches into a fresh integration branch.
3. **Polyglot Validation:** Executes specialized health checks for every technology stack found in the monorepo after every merge.

---

## 🧪 Validation Suites

The engine automatically detects and validates components across multiple technology stacks:

| Stack | Check Mechanism |
| :--- | :--- |
| **Node.js** | `npm build` (recursive discovery) |
| **Python** | `venv` isolation + `pytest` |
| **PHP / Laravel** | `composer validate` + `artisan test` + `migrate` |
| **Rust** | `cargo test` |
| **Dart / Flutter** | `pub get` + `dart test` |
| **C / Make** | `make test` |
| **Shell** | `bash -n` syntax linting |
| **Config** | `yamllint` (Workflows) + `jq` (JSON validation) |

---

## ⚙️ Configuration

The behavior of the integration engine is controlled by a centralized configuration file in the project root. The engine supports both YAML (`github_configuration.yaml` / `github_configuration.example.yaml`) and JSON (`.github/configuration.json`) structures.

### 📂 Centralized YAML Config

Update the settings in [`github_configuration.yaml`](../github_configuration.yaml) to manage:

* **Target Branch**: The base branch for integration.
* **Branch Prefixes**: Which branches to include in the merge.
* **Output Prefix**: The prefix for the resulting integration branch.
* **Allow Manual Run**: Boolean (`true`/`false`) to permit or block manual triggers from the GitHub UI.
* **Pull Request Settings**: Configuration for automatic pull request creation upon successful validation.
* **Code Checks**: A granular map of validation suites (e.g., `laravel`, `node`, `python`) each with an `enabled` flag.

```yaml
integration:
  enabled: true
  target_branch: "develop"
  branch_prefixes:
    - "feat/"
    - "chore/"
    - "bug/"
    - "docs/"
    - "test/"
  output_branch_prefix: "nightly"
  output_branch_append_date: true
  allow_manual_run: true
  pull_request:
    enabled: true
    to_branch: "develop"
    title: "Nightly Update"
    body: "Automated PR to update develop from nightly snapshot"

code_checks:
  node:
    enabled: true
  python:
    enabled: true
  laravel:
    enabled: true
  rust:
    enabled: true
  dart:
    enabled: true
  makefile:
    enabled: true
  bash:
    enabled: true
  markdown:
    enabled: true
  config:
    enabled: true
```

---

## 🐍 Python Action Architecture

To ensure superior reliability, maintainability, and verbose logging, all custom GitHub Actions in this repository have been migrated from inline Bash blocks to dedicated **Python 3** scripts. 

Each action is self-contained with a standardized structure:
- **[action.yaml](file:///home/mozrin/Code/github-moztopia/actions/code-validation/action.yaml)**: Defines inputs, outputs, and shell execution hooks that invoke the Python script.
- **Python Scripts**: Located alongside their respective `action.yaml` files, utilizing the Python standard library to recursively scan directories, parse configs, manage subprocess execution, and write to `GITHUB_OUTPUT` / `GITHUB_ENV` variables cleanly.

### Key Python Components:
- **[`setup_env.py`](file:///home/mozrin/Code/github-moztopia/actions/setup-environment/setup_env.py)**: Performs lightweight parse of the project configuration, sets up Git configuration, and exports environment gates (e.g., `CHECK_NODE=true`) to control downstream execution.
- **[`git_merge_prefixes.py`](file:///home/mozrin/Code/github-moztopia/actions/git-merge-prefixes/git_merge_prefixes.py)**: Safely merges all matching remote branches sequentially, managing merge flows, dates, and integration branches.
- **Polyglot Checkers**: Dedicated validation checkers (`node_check.py`, `python_check.py`, `laravel_check.py`, `rust_check.py`, `dart_check.py`, `makefile_check.py`, `bash_check.py`, `markdown_check.py`, `config_check.py`) that run the validation suites with full directory discovery and error logging.
- **[`create_pr.py`](file:///home/mozrin/Code/github-moztopia/actions/create-pull-request/create_pr.py)**: Integrates with the GitHub CLI (`gh`) to check for open PRs, edit existing ones, or generate fresh pull requests.
- **[`build_bot.py`](file:///home/mozrin/Code/github-moztopia/actions/build-bot/build_bot.py)**: Performs speculative, incremental merges of all remote `build/*` branches into a dynamically named daily target branch, resetting conflict or check-failed merges, and pushes successful outcomes to the remote repository.

---

## 💡 Best Practices

* **Monitor Results:** Check the Actions tab daily for failures in the integration branches; these often signal upcoming merge conflicts or cross-module breakages.
* **Local Validation:** Before pushing to a featured branch, run the language-specific test command relevant to your module to minimize integration failures.
* **Manual Triggers:** Use the **"Run workflow"** button in GitHub Actions to manually trigger the integration if you need to validate a complex multi-branch feature set immediately.

---
> [!TIP]
> If a specific branch is causing consistent failures, consider moving it to a prefix not included in the `github_configuration.yaml` until the integration issues are resolved.
