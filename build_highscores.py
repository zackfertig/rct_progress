# Build OpenRCT2 highscores.dat v2 from an RCT1 CSV
# CSV columns expected: filename,name,company_value,winner
# - filename: scenario filename (SC*.SC4), case preserved
# - name: scenario display name (optional)
# - company_value: integer currency units (e.g., 80000 for $80,000)
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
from typing import BinaryIO

VERSION = 2
INT64_MIN = -9223372036854775808


def write_cstring(fh, s: str, encoding='utf-8'):
    data = (s or '').encode(encoding, errors='replace')
    fh.write(data)
    fh.write(b'\x00')


def to_money64(company_value_field: str | int | float | None, *, scale: int = 10) -> int:
    if company_value_field is None:
        return 0
    s = str(company_value_field).strip()
    if s == '':
        return 0
    try:
        v = int(float(s))
    except ValueError:
        return 0
    # money64 internal units: typically value ×10; allow overriding via scale
    return int(v * scale)


def build_from_rows(rows: list[dict], out_path: Path, *, value_scale: int = 10):
    filtered = [r for r in rows if (r.get('filename') or '').strip() and (r.get('winner') or '').strip()]

    with open(out_path, 'wb') as f:
        # header
        f.write(struct.pack('<I', VERSION))
        f.write(struct.pack('<I', len(filtered)))

        for r in filtered:
            file_name_only = Path(r.get('filename').strip()).name
            winner = r.get('winner', '').strip()
            money64 = to_money64(r.get('company_value'), scale=value_scale)

            write_cstring(f, file_name_only)
            write_cstring(f, winner)
            f.write(struct.pack('<q', money64))      # int64 little-endian
            f.write(struct.pack('<q', INT64_MIN))    # timestamp

    print(f"highscores.dat written: {out_path}")
    print(f"Entries: {len(filtered)}")


def _read_cstring(fh: BinaryIO) -> str:
    bs = bytearray()
    while True:
        b = fh.read(1)
        if not b or b == b"\x00":
            break
        bs += b
    return bs.decode('utf-8', errors='replace')


def verify_highscores(path: Path, *, limit: int = 10):
    with open(path, 'rb') as f:
        ver = int.from_bytes(f.read(4), 'little')
        cnt = int.from_bytes(f.read(4), 'little')
        print(f"version={ver} entries={cnt}")
        n = min(cnt, max(0, limit))
        for i in range(n):
            fn = _read_cstring(f)
            name = _read_cstring(f)
            val = int.from_bytes(f.read(8), 'little', signed=True)
            ts = int.from_bytes(f.read(8), 'little', signed=True)
            # Print value in display currency units by dividing by 10
            print(f"{i+1:2d}. {fn:20s} {name:20s} value={val/10:.0f}")


def build(csv_path: Path, out_path: Path, *, value_scale: int = 10):
    with open(csv_path, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    build_from_rows(rows, out_path, value_scale=value_scale)


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
    parser.add_argument('--scale', type=int, default=10, help='CSV company_value scale factor (default: 10). For CSS0.DAT, scaling is not applied (already internal units).')
    parser.add_argument('--verify', action='store_true', help='After writing, read highscores.dat and print a brief summary')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of entries to display during --verify (default: 10)')
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.css0:
        rows = rows_from_css0(Path(args.css0))
        # CSS0 company_value is already in internal units (×10), so do not rescale.
        build_from_rows(rows, out, value_scale=1)
    else:
        csv_in = Path(args.input)
        build(csv_in, out, value_scale=args.scale)

    if args.verify:
        verify_highscores(out, limit=args.limit)
