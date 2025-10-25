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
python -m rct_progress.cli -i CSS0.DAT -o css0_parsed.csv
```

Or install the package locally and use the console script:

```powershell
python -m pip install -e .
rct-progress -i CSS0.DAT -o css0_parsed.csv
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
- `process_file(input_path: Path, out_csv: Path, verbose: bool=False) -> List[dict]` — end-to-end processing.

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
