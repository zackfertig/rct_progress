# Build OpenRCT2 highscores.dat v2 from an RCT1 CSV
# CSV columns expected: filename,name,company_value,winner
# - filename: scenario filename (SC*.SC4), case preserved
# - name: scenario display name (optional)
# - company_value: integer internal units (display currency ×10)
# - winner: player name; if empty, entry won't be written
#
# Output: highscores.dat alongside the CSV
# Place at: %USERPROFILE%\Documents\OpenRCT2\highscores.dat
#
# File format (ScenarioRepository.cpp as of v0.4.27):
# uint32 version = 2;
# uint32 count;
# repeated count times:
#   cstring fileName;          // scenario file name only (e.g., sc0.sc4 or FOREST FRONTIERS.SC6)
#   cstring name;              // player name
#   money64 company_value;     // int64, internal units (currency * 10)
#   datetime64 timestamp;      // int64; use minimum to indicate legacy/unknown time
#
# Strings are written as raw bytes followed by a single 0x00 terminator (no length prefix).
# money64/datetime64 are 8-byte little-endian signed integers.

import csv
import struct
from pathlib import Path
import argparse
import sys
import tempfile

VERSION = 2
INT64_MIN = -9223372036854775808


def write_cstring(fh, s: str, encoding='utf-8'):
    data = (s or '').encode(encoding, errors='replace')
    fh.write(data)
    fh.write(b'\x00')


def to_money64(company_value_field: str | int | float | None) -> int:
    if company_value_field is None:
        return 0
    s = str(company_value_field).strip()
    if s == '':
        return 0
    try:
        v = int(float(s))
    except ValueError:
        return 0
    # money64 internal units expected directly (×10 already applied)
    return int(v)


def build_from_rows(rows: list[dict], out_path: Path):
    filtered = [r for r in rows if (r.get('filename') or '').strip() and (r.get('winner') or '').strip()]

    with open(out_path, 'wb') as f:
        # header
        f.write(struct.pack('<I', VERSION))
        f.write(struct.pack('<I', len(filtered)))

        for r in filtered:
            file_name_only = Path(r.get('filename').strip()).name
            winner = r.get('winner', '').strip()
            money64 = to_money64(r.get('company_value'))

            write_cstring(f, file_name_only)
            write_cstring(f, winner)
            f.write(struct.pack('<q', money64))      # int64 little-endian
            f.write(struct.pack('<q', INT64_MIN))    # timestamp

    print(f"highscores.dat written: {out_path}")
    print(f"Entries: {len(filtered)}")


def build(csv_path: Path, out_path: Path):
    with open(csv_path, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    build_from_rows(rows, out_path)


def rows_from_css0(css0_path: Path) -> list[dict]:
    """Parse CSS0.DAT and return rows compatible with build_from_rows.

    Tries to import rct_progress.core.process_file from this repo. If the
    package is not importable, the function adjusts sys.path to include ./src.
    """
    try:
        from rct_progress.core import process_file  # type: ignore
    except Exception:
        # Add ./src to sys.path when running directly from repo root
        repo_root = Path(__file__).resolve().parent
        src_path = (repo_root / 'src').resolve()
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        from rct_progress.core import process_file  # type: ignore

    # Write CSV to a temp file but primarily use returned rows
    with tempfile.TemporaryDirectory() as td:
        tmp_csv = Path(td) / 'css0_parsed.csv'
        rows = process_file(css0_path, tmp_csv, verbose=False, keep_intermediate=False)
    # Ensure dict keys conform: filename, name, company_value, winner
    normalized = []
    for r in rows:
        normalized.append({
            'filename': r.get('filename', ''),
            'name': r.get('name', ''),
            'company_value': r.get('company_value', 0),
            'winner': r.get('winner', ''),
        })
    return normalized


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build OpenRCT2 highscores.dat (v2) from RCT1 CSV or CSS0.DAT')
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument('-i', '--input', help='Path to input CSV (filename, name, company_value, winner)')
    src.add_argument('--css0', help='Path to CSS0.DAT to parse directly')
    parser.add_argument('-o', '--output', required=True, help='Path to output highscores.dat')
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.css0:
        rows = rows_from_css0(Path(args.css0))
        # CSS0 company_value is already in internal units (×10)
        build_from_rows(rows, out)
    else:
        csv_in = Path(args.input)
        # CSV company_value must already be internal units (×10)
        build(csv_in, out)
