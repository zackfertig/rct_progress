# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 — 2025-10-29
- Added: Portable binaries (Windows/macOS/Linux) built with PyInstaller and attached to Releases.
- Added: Drag-and-drop support in rct-highscores binary:
	- Drop CSS0.DAT to generate highscores.dat into the default OpenRCT2 user folder.
	- Drop CSS0.DAT + highscores.dat together to merge and write back to the provided highscores file.
- Added: Cross-platform README with Windows/macOS/Linux examples and install paths.
- Changed: Merge behavior documented more clearly; backup guidance included.
- Changed: Preserve negative company values end-to-end and write as signed money64.
- Fixed: Avoid 10× inflation on CSS0 route by not re-scaling internal units.

## 0.1.1 — 2025-10-29
- Added: `--merge` to combine new entries with an existing `highscores.dat`.
	- Matches by filename (case-insensitive) and keeps the higher company value; winner/timestamp from the winning entry are preserved.
- Changed: Preserve negative company values end-to-end; values from CSS0 are read as signed and written as signed money64 in `highscores.dat`.
- Fix: Avoid 10× inflated company values when using `--css0` by not re-scaling already-internal units.
- CSV path now requires `company_value` in internal units (display ×10); the previous CSV scaling option has been removed.
- Documentation updates and packaging polish.

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

