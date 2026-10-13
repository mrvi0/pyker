# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Community docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- GitHub issue/PR templates, CI workflow, Dependabot config

## [1.2.0] - 2026-10-13

### Added

- Real `--auto-restart` via background watcher (`pyker watch`)
- Modular package layout (`pyker/` package)
- Smoke tests for start/stop/state/resurrect

### Changed

- Installers install the package via pip instead of copying a single script
- Demo scripts cleaned up

## [1.1.0] - 2026-10-13

### Added

- Start-on-boot support: `enable` / `disable`, `startup` / `unstartup`, `resurrect`
- `--on-boot` flag for `start`

## [1.0.0] - 2026-10-13

### Added

- `pyproject.toml` packaging for `uv tool install` / `uvx`
- Documentation for uv/uvx installation

### Fixed

- Broken install URL (`username/pyker` → `mrvi0/pyker`)

[Unreleased]: https://github.com/mrvi0/pyker/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/mrvi0/pyker/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mrvi0/pyker/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mrvi0/pyker/releases/tag/v1.0.0
