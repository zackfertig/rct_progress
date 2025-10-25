rct_progress
============

Small utilities to decompress, decrypt and parse RollerCoaster Tycoon
`CSS0.DAT` progress/scenario archives. Tested with RCT1 with Loopy
Landscapes and Added Attractions installed

Features
--------
- Decompress RCT RLE-compressed data
- Reverse the simple DWord-level obfuscation used in the archive
- Parse scenario tables and write a CSV of filenames, scenario names and metadata

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
