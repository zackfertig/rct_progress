# Import RCT1 progress into OpenRCT2

Convert RollerCoaster Tycoon 1 progress into OpenRCT2’s highscores.dat so Classic/AA/LL scenarios show as completed with the correct winner's name and park value.

Tested with OpenRCT2 v0.4.27. Commands are provided for Windows (PowerShell) and macOS/Linux (bash). Use whichever matches your shell, with Python 3.8+ installed. Platform-specific binaries that support drag and drop are also released.

## What’s new in 0.2.2

- CI: Single unified workflow builds binaries and publishes Releases with auto-generated notes.
- CI: Stabilized PyInstaller usage across OSes; fixed Windows/macOS interpreter mismatch.
- Linux: AppImage temporarily disabled for this tag to unblock the release; CLI one-file binary still provided.

## What’s new in 0.2.1

- macOS: Native .app “droplet” for true drag‑and‑drop (no Terminal needed).
- Linux: AppImage with desktop integration and multi‑file drag‑and‑drop.
- Windows: Fixed binary naming — .exe preserved with platform suffix in releases.

## Downloads

Always get the latest prebuilt binaries from the Releases page:

- Latest release: https://github.com/zackfertig/rct_progress/releases/latest

The Release body includes direct links for Windows, macOS (.app droplet and CLI), and Linux (CLI; AppImage may be temporarily unavailable for some tags) for the current tag.

## Quick start: Drag & Drop (no Python)

- Download the `rct-highscores` binary for your platform from the Releases page.
- Drag and drop your files onto `rct-highscores`:
	- Single file: Drop `CSS0.DAT` to generate a `highscores.dat` in your OpenRCT2 user folder
		- Windows: `%USERPROFILE%\Documents\OpenRCT2\highscores.dat`
		- macOS: `~/Library/Application Support/OpenRCT2/highscores.dat`
		- Linux: `~/.config/OpenRCT2/highscores.dat`
	- Two files: Drop `CSS0.DAT` and an existing `highscores.dat` together to MERGE and write back to the dropped highscores path
- Tip: Back up your existing highscores.dat before merging.
- macOS (.app): Download `rct-highscores.app` and drag files onto it (Finder or Dock). If Gatekeeper warns, right‑click the app → Open. Advanced: `xattr -dr com.apple.quarantine rct-highscores.app`.
- Linux (AppImage): When available, download `rct-highscores-*.AppImage`, mark executable, and double‑click. Drag files onto the launcher/icon if your desktop supports it. First run may offer “Integrate” into your menu.

## 1) Generate highscores.dat (recommended)

Prerequisites
- Python 3.8+ (Windows/macOS/Linux)
- Either:
	- CSS0.DAT from RCT1 (preferred), or
	- A CSV with columns: `filename`, `name` (optional), `company_value`, `winner`

Prebuilt binaries (no Python required)
- For convenience, portable binaries may be attached to Releases (Windows/macOS/Linux):
	- Windows: `rct-highscores.exe` (drag‑and‑drop onto the .exe)
	- macOS: `rct-highscores.app` droplet (drag files onto the app)
	- Linux: `rct-highscores-<arch>.AppImage` (make executable; optional menu integration)
	- Also available: `rct-progress` (CSS0.DAT → CSV parser)
- Usage is the same as the Python scripts; just replace the python invocation with the binary:
	- Windows: `./rct-highscores.exe --css0 "...\DATA\CSS0.DAT" -o ./outdir/highscores.dat --merge`
	- macOS (CLI one‑file): `./rct-highscores --css0 "/path/.../DATA/CSS0.DAT" -o ./outdir/highscores.dat --merge`
	- Linux (CLI one‑file): `./rct-highscores --css0 "/path/.../DATA/CSS0.DAT" -o ./outdir/highscores.dat --merge`
	- macOS Gatekeeper: for the CLI binary, remove quarantine and make it executable if needed: `xattr -dr com.apple.quarantine ./rct-highscores; chmod +x ./rct-highscores`
	- Linux permissions: mark CLI binary or AppImage executable if needed: `chmod +x ./rct-highscores` or `chmod +x ./rct-highscores-*.AppImage`
 - Drag-and-drop (binaries only):
	 - Drop a single `CSS0.DAT` onto `rct-highscores` to generate `highscores.dat` into your default OpenRCT2 user folder:
		 - Windows: `%USERPROFILE%\Documents\OpenRCT2\highscores.dat`
		 - macOS: `~/Library/Application Support/OpenRCT2/highscores.dat`
		 - Linux: `~/.config/OpenRCT2/highscores.dat`
	 - Drop both `CSS0.DAT` and an existing `highscores.dat` onto `rct-highscores` to merge and write to the given highscores path.

OS‑native packages details
- macOS `.app` droplet
  - Download `rct-highscores.app` from Releases and drag `CSS0.DAT` (and optionally an existing `highscores.dat`) onto it.
  - First‑run security: right‑click the app → Open to bypass Gatekeeper; or remove quarantine via Terminal: `xattr -dr com.apple.quarantine rct-highscores.app`.
  - Outputs to your OpenRCT2 user folder when only `CSS0.DAT` is provided; merges if both files are dropped.
- Linux AppImage
  - Download `rct-highscores-*.AppImage`, then: `chmod +x rct-highscores-*.AppImage` and double‑click.
  - Optional: run once to integrate into your desktop menu; after integration you can drag files onto the launcher/icon if supported by your environment.
  - As with other binaries, a single `CSS0.DAT` generates to the default OpenRCT2 folder; adding a `highscores.dat` performs an in‑place merge.

Usage
- Preferred (after installing the package locally):
```bash
rct-highscores --css0 "/path/to/.../CSS0.DAT" -o ./outdir/highscores.dat --merge
# or from CSV
rct-highscores -i ./outdir/css0_parsed_split.csv -o ./outdir/highscores.dat
```

In-place (from this repo folder)
Usage examples (PowerShell/Bash)
 Direct from CSS0.DAT (recommended):
	- Windows PowerShell:
		```powershell
		rct-highscores --css0 "[...]\RollerCoaster Tycoon\DATA\CSS0.DAT" -o .\outdir\highscores.dat --merge
		```
	- macOS/Linux:
		```bash
		rct-highscores --css0 "/path/to/RollerCoaster Tycoon/DATA/CSS0.DAT" -o ./outdir/highscores.dat --merge
		```

 From CSV:
	- Windows PowerShell:
		```powershell
		rct-highscores -i .\outdir\css0_parsed_split.csv -o .\outdir\highscores.dat --merge
		```
	- macOS/Linux:
		```bash
		rct-highscores -i ./outdir/css0_parsed_split.csv -o ./outdir/highscores.dat --merge
		```

Install into OpenRCT2
- Windows (PowerShell):
```powershell
Copy-Item .\outdir\highscores.dat "$env:USERPROFILE\Documents\OpenRCT2\highscores.dat" -Force
```
- macOS (bash):
```bash
install -d "$HOME/Library/Application Support/OpenRCT2"
cp -f ./outdir/highscores.dat "$HOME/Library/Application Support/OpenRCT2/highscores.dat"
```
- Linux (bash):
```bash
install -d "$HOME/.config/OpenRCT2"
cp -f ./outdir/highscores.dat "$HOME/.config/OpenRCT2/highscores.dat"
```
Restart OpenRCT2.

Notes
- Matching is by scenario file name only (e.g., `sc0.sc4`). The scenario must exist and be indexed by OpenRCT2.
- Scaling:
- CSV path: `company_value` must be specified in internal units (display currency ×10).
- CSS0 path: values are already in internal units (×10); no extra scaling is applied (prevents 10× inflation).
- Negative values: supported and preserved end-to-end; they are written as signed money64 values in highscores.dat.
- If you also have legacy `scores.dat`, `highscores.dat` takes precedence.
- Merging behavior (`--merge`):
	- One entry per scenario filename (case-insensitive)
	- When duplicates exist, the higher company value wins (positives beat negatives; among negatives, the less negative wins)
	- Winner name comes from the winning entry
	- Existing timestamps are preserved; new entries use a minimal timestamp
	- Tip: Back up `%USERPROFILE%\Documents\OpenRCT2\highscores.dat` before running a merge

Troubleshooting (AA scenarios)
- Symptom: AA scenarios appear completed but can’t be selected, or you see duplicates (e.g., Funtopia).
- Cause: duplicate SC4 files in scanned folders (e.g., `Old_SC40.SC4` … `Old_SC69.SC4`).
- Fix:
	1) Close OpenRCT2.
	2) Remove/archive duplicates so only canonical files remain (e.g., `sc40.sc4` … `sc69.sc4`).
	3) (Optional) Delete `%USERPROFILE%\Documents\OpenRCT2\scenarios.idx` to force re-index.
	4) Restart OpenRCT2.

Legacy RCT2 scores.dat
- For RCT1 progress, prefer OpenRCT2’s native highscores.dat. The legacy scores.dat import path isn’t required for SC4 and is discouraged.

## 2) Parse CSS0.DAT to CSV (library CLI)

Small utilities to decrypt, decompress, and parse RCT1’s `CSS0.DAT` into a CSV.

Quick start
- Cross-platform (bash/PowerShell):
```bash
# in-place run (from repo root)
python3 -m rct_progress.cli -i CSS0.DAT -o css0_parsed.csv

# optional: install locally and use console script
python3 -m pip install -e .
rct-progress -i CSS0.DAT -o css0_parsed.csv
```

Logging & intermediates
- `-v/--verbose` increases logging.
- `-k/--keep-intermediate` writes intermediate raw binaries next to the input.

Examples
```bash
rct-progress -i CSS0.DAT -o css0_parsed.csv -v
rct-progress -i CSS0.DAT -o css0_parsed.csv -v -k
# alias: --output can be used instead of --out
rct-progress -i CSS0.DAT --output css0_parsed.csv
```

Output format
- CSV columns: `index, filename, name, company_value, winner`.

API reference
- See `src/rct_progress/core.py`:
	- `rle_decompress(data: bytes) -> bytes`
	- `decrypt_dwords_le(data: bytes) -> bytes`
	- `verify_checksum(data: bytes, expected_checksum: int) -> (bool, int)`
	- `process_file(input_path: Path, out_csv: Path, verbose: bool=False, *, keep_intermediate: bool=False) -> List[dict]`

## Development

Build
```bash
python3 -m pip install --upgrade build
python3 -m build
```

Contributing
- Please open issues or PRs. Small, well-scoped changes and tests are preferred.

License
- MIT — see `LICENSE`.

Developer notes
- Processing order mirrors the original game pipeline:
	1) Verify checksum on compressed data (last 4 bytes are the checksum)
	2) RLE-decompress the compressed body
	3) Decrypt per 32-bit little-endian dword: ROTL32(5), then subtract 0x39393939
	4) Parse fixed tables and write CSV
- Data layout (see `core.py`):
	- Filenames @ 0x0000 (16 bytes each)
	- Scenario names @ 0x0800 (64 bytes each)
	- Company values @ 0x2800 (DWORDs)
	- Winners @ 0x2A00 (32 bytes each)
	- Max entries: 128
- Programmatic use:
	- `parse_tables(decrypted: bytes) -> List[Row]`
	- `parse_and_write(decrypted: bytes, out_csv: Path)`

- Generate highscores.dat (dev quick ref):
	- Format (OpenRCT2 v2):
		- uint32 version = 2
		- uint32 count
		- repeated per entry:
			- cstring fileName (scenario file name only, e.g., `sc0.sc4`)
			- cstring name (player name)
			- int64 company_value (internal units = display currency × 10)
			- int64 timestamp (use INT64_MIN for unknown)
	- Build directly (no install) using module:
		```powershell
		python -m rct_progress.highscores --css0 "[...]\RollerCoaster Tycoon\DATA\CSS0.DAT" -o .\outdir\highscores.dat
		```
	- Or use the installed console script:
		```powershell
		rct-highscores --css0 "[...]\RollerCoaster Tycoon\DATA\CSS0.DAT" -o .\outdir\highscores.dat
		```
	- Notes:
		- CSV path requires company_value in internal units (display ×10).
		- CSS0 path writes values as-is in internal units (display ×10).
		- Negative values are preserved end-to-end and written as signed money64.
		- `--merge` merges with an existing highscores.dat, keeping the entry with the higher company value per scenario and preserving timestamps where present.
