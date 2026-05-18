# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Implemented speculative integration build-bot workflow `workflows/build-bot.yaml` and composite action `actions/build-bot`.
- Standardized action files to `.yaml` extensions and cleaned all internal paths/references.
- Developed brand-new Python-based `check-gate` and `setup-environment` actions, fully replacing legacy inline bash code.
