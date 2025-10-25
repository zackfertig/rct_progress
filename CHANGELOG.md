# Changelog

All notable changes to this project will be documented in this file.

## [0.0.2] - 2025-10-25
### Changed
- Logging ergonomics: intermediate file writes now log at DEBUG; a single INFO line reports CSV output.
- CLI behavior: `--verbose` only increases logging; intermediates are written only with `--keep-intermediate`.
- Company value typing normalized: `company_value` is now Optional[int] in memory and rendered as empty in CSV when missing.
- README: added Developer notes section and documented `--keep-intermediate` and `--output` alias.

## [0.0.1] - 2025-10-25
### Added
- Initial extraction and tooling to decompress and decrypt `CSS0.DAT`.
- `rct_progress.core` and `rct_progress.cli` modules.
- `css0_parsed.csv` generation tool and example output.
- README, CONTRIBUTING, license.

