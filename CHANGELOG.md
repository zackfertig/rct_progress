# Changelog

All notable changes to this project will be documented in this file.

## 2025-10-28
## 0.1.0 — 2025-10-28
 - Unify documentation into a single `README.md` with end-to-end instructions.
 - Add direct `CSS0.DAT` → `highscores.dat` support to `build_highscores.py`.
 - Switch `build_highscores.py` to CLI arguments: `-i/--input` (CSV) or `--css0` (DAT) and `-o/--output`.
 - Mark legacy RCT2 scores.dat approach as informational only; removed old legacy READMEs.
	- Verified end-to-end with OpenRCT2 v0.4.27 on Windows.

All notable changes to this project will be documented in this file.
- CLI behavior: `--verbose` only increases logging; intermediates are written only with `--keep-intermediate`.
- Company value typing normalized: `company_value` is now Optional[int] in memory and rendered as empty in CSV when missing.
- README: added Developer notes section and documented `--keep-intermediate` and `--output` alias.
- `rct_progress.core` and `rct_progress.cli` modules.
- `css0_parsed.csv` generation tool and example output.
- README, CONTRIBUTING, license.

