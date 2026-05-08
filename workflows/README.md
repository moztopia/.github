# 🌙 Automated Integration & Validation

Welcome to the automated heart of our repository's cross-component integration. This directory contains the **Automated Integration** engine, a comprehensive workflow designed to ensure seamless compatibility across our polyglot codebase.

---

## 🛠️ Workflow Overview

**File:** [`automated_integration.yaml`](./automated_integration.yaml)  
**Triggers:** Scheduled (see YAML) or Manual Dispatch via `workflow_dispatch`.

The Automated Integration is our comprehensive validation engine. It performs a "Deep Merge" of all active feature branches to detect integration conflicts and cross-project regressions before they reach the main development branches.

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

The behavior of the integration engine is controlled by a centralized configuration file.

### 📂 Centralized Config

Update the settings in [`.github/configuration.json`](../configuration.json) to manage:

* **Target Branch**: The base branch for integration.
* **Branch Prefixes**: Which branches to include in the merge.
* **Output Prefix**: The prefix for the resulting integration branch.
* **Allow Manual Run**: Boolean (`true`/`false`) to permit or block manual triggers from the GitHub UI.
* **Code Checks**: A granular map of validation suites (e.g., `laravel`, `node`, `python`) each with an `enabled` flag.

```json
{
    "integration": {
        "enabled": true,
        "target_branch": "develop",
        "branch_prefixes": ["feat/", "chore/", "bug/", "docs/", "test/"],
        "output_branch_prefix": "nightly+",
        "allow_manual_run": true
    },
    "code_checks": {
        "node": { "enabled": true },
        "python": { "enabled": true },
        "laravel": { "enabled": true },
        "rust": { "enabled": true },
        "dart": { "enabled": true },
        "makefile": { "enabled": true },
        "bash": { "enabled": true },
        "markdown": { "enabled": true },
        "config": { "enabled": true }
    }
}
```

---

## 💡 Best Practices

* **Monitor Results:** Check the Actions tab daily for failures in the integration branches; these often signal upcoming merge conflicts or cross-module breakages.
* **Local Validation:** Before pushing to a featured branch, run the language-specific test command relevant to your module to minimize integration failures.
* **Manual Triggers:** Use the **"Run workflow"** button in GitHub Actions to manually trigger the integration if you need to validate a complex multi-branch feature set immediately.

---
> [!TIP]
> If a specific branch is causing consistent failures, consider moving it to a prefix not included in the `configuration.json` until the integration issues are resolved.
