# Import RCT1 progress into OpenRCT2

This repo provides a script to convert an RCT1 progress CSV into OpenRCT2's highscores.dat (v2), so Classic/AA/LL scenarios (e.g., Forest Frontiers) show as completed.

Tested with OpenRCT2 v0.4.27 on Windows.

## Prerequisites
- Python 3.8+ on Windows
- An RCT1 CSV with columns: `filename`, `name` (optional), `company_value`, `winner`

## Generate highscores.dat (recommended)
OpenRCT2 stores highscores in a binary file with the following layout (version 2):
- uint32 version = 2
- uint32 count
- For each entry:
  - cstring fileName (scenario file name only, e.g., `sc0.sc4`)
  - cstring name (player name)
  - int64 company_value (value ×10)
  - int64 timestamp (use INT64_MIN for legacy/unknown)

### Usage
```powershell
# From this repo folder
py .\build_highscores.py -i .\outdir\css0_parsed_split.csv -o .\outdir\highscores.dat
```

Or convert directly from CSS0.DAT without creating a CSV first (with a quick verify):

```powershell
py .\build_highscores.py --css0 "[...]\RollerCoaster Tycoon\\DATA\\CSS0.DAT" -o .\outdir\highscores.dat --verify --limit 10
```

Then install into OpenRCT2:
```powershell
Copy-Item .\outdir\highscores.dat "$env:USERPROFILE\Documents\OpenRCT2\highscores.dat" -Force
```
Restart OpenRCT2.

### Notes
- Matching uses only the scenario file name (e.g., `sc0.sc4`). The scenario must be present and indexed in OpenRCT2.
- Scaling:
	- CSV path: `company_value` is treated as whole currency units and scaled by `--scale` (default 10) into internal units.
	- CSS0 path: values are already in internal units (×10), so the script writes them without additional scaling (no 10× inflation).

	- New in 0.1.1: `--verify` reads the generated `highscores.dat` and prints the header and first N entries so you can sanity check values without extra tools.
- If you also have legacy `scores.dat`, highscores.dat takes precedence.

### Troubleshooting (AA scenarios)
Symptoms
- AA scenarios appear completed but not selectable, or some appear twice (e.g., Funtopia).

Cause
- Duplicate SC4 files (e.g., `Old_SC40.SC4` … `Old_SC69.SC4`) in scanned folders.

Fix
1) Close OpenRCT2.
2) Remove or archive duplicates so only canonical files remain (e.g., `sc40.sc4` … `sc69.sc4`).
3) (Optional) Delete `%USERPROFILE%\Documents\OpenRCT2\scenarios.idx` to force a rebuild.
4) Restart OpenRCT2.

## Notes on legacy RCT2 scores.dat
If you specifically need to generate an RCT2-style scores.dat for legacy import, prefer using OpenRCT2's native highscores.dat for RCT1 progress. The legacy route is not required and is generally discouraged for SC4.
rct_progress
============

Small utilities to decompress, decrypt and parse RollerCoaster Tycoon
`CSS0.DAT` progress/scenario archives. Tested with RCT1 with Loopy
Landscapes and Added Attractions installed

Features
--------
- Decrypts the `CSS0.DAT` from RollerCoaster Tycoon 1 so that the player's progress can be transferred to OpenRCT2

Quick start
-----------

Run the CLI against a `CSS0.DAT` file in the repository root:

```powershell
# in-place run without installing (from repo root)
python -m rct_progress.cli -i CSS0.DAT -o css0_parsed.csv
```

Or install the package locally and use the console script:

```powershell
python -m pip install -e .

# console script
rct-progress -i CSS0.DAT -o css0_parsed.csv
```

Logging and intermediates
-------------------------
- `--verbose` (or `-v`) enables additional logging.
- Intermediate raw binaries are only written when you also pass `--keep-intermediate` (or `-k`).

Examples:

```powershell
# verbose logging only; no intermediate files are written
rct-progress -i CSS0.DAT -o css0_parsed.csv -v

# verbose logging and keep intermediate files next to the input path
rct-progress -i CSS0.DAT -o css0_parsed.csv -v -k

# the CLI also accepts --output as an alias for --out
rct-progress -i CSS0.DAT --output css0_parsed.csv
```

Example output
--------------
The tool writes `css0_parsed.csv` with columns: `index, filename, name, company_value, winner`.

API reference
-------------
Primary functions are in `src/rct_progress/core.py`:

- `rle_decompress(data: bytes) -> bytes` — decompresses RLE payload (expects checksum as last 4 bytes).
- `decrypt_dwords_le(data: bytes) -> bytes` — decrypts 32-bit little-endian DWords.
- `verify_checksum(data: bytes, expected_checksum: int) -> (bool, int)` — validates compressed-body checksum.
- `process_file(input_path: Path, out_csv: Path, verbose: bool=False, *, keep_intermediate: bool=False) -> List[dict]` — end-to-end processing.

Packaging and publishing
-----------------------
The project uses the `src/` layout and a minimal `pyproject.toml` for building.

Build a wheel:

```powershell
python -m pip install --upgrade build
python -m build
```

Publishing to PyPI can be done via `twine` after creating an account and API token.

Contributing
------------
Please open issues or PRs. Small, well-scoped changes and tests are preferred.

License
-------
MIT — see the `LICENSE` file for details.

Developer notes
---------------
- Processing order is critical and matches the original game’s pipeline:
	1) Verify checksum on the compressed data (trailing 4 bytes are the checksum).
	2) RLE-decompress the compressed body.
	3) Decrypt the decompressed stream per 32-bit little-endian DWord: `ROTL32(5)` then subtract `0x39393939`.
	4) Parse fixed tables and write CSV.
- Data layout constants (see `core.py`):
	- Filenames at 0x0000 (16 bytes each)
	- Scenario names at 0x0800 (64 bytes each)
	- Company values at 0x2800 (DWORDs)
	- Winners at 0x2A00 (32 bytes each)
	- Max entries: 128
- Programmatic use:
	- `parse_tables(decrypted: bytes) -> List[Row]` returns parsed rows without writing files.
	- `parse_and_write(decrypted: bytes, out_csv: Path)` is a convenience wrapper.
	- The CLI simply wires these building blocks together.
