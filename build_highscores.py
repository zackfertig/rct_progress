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
from typing import BinaryIO, Dict, Tuple

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


# --- Merge support ---
def _read_cstring(fh: BinaryIO) -> str:
    bs = bytearray()
    while True:
        b = fh.read(1)
        if not b or b == b"\x00":
            break
        bs += b
    return bs.decode('utf-8', errors='replace')


def load_highscores(path: Path) -> Dict[str, Tuple[str, str, int, int]]:
    """Load highscores.dat into a dict keyed by lowercase filename.

    Value tuple: (filename_original, winner_name, company_value, timestamp)
    """
    result: Dict[str, Tuple[str, str, int, int]] = {}
    if not path.exists():
        return result
    with open(path, 'rb') as f:
        ver = int.from_bytes(f.read(4), 'little')
        if ver != VERSION:
            # Proceed but note: we only write v2; loader will re-write v2
            pass
        cnt = int.from_bytes(f.read(4), 'little')
        for _ in range(cnt):
            fn = _read_cstring(f)
            name = _read_cstring(f)
            val = int.from_bytes(f.read(8), 'little', signed=True)
            ts = int.from_bytes(f.read(8), 'little', signed=True)
            result[fn.lower()] = (fn, name, val, ts)
    return result


def best_map_from_rows(rows: list[dict]) -> Dict[str, Tuple[str, str, int, int]]:
    """Reduce rows to best-by-filename map in internal units, timestamp=INT64_MIN.

    For duplicates in rows, keep the entry with the higher company_value.
    """
    best: Dict[str, Tuple[str, str, int, int]] = {}
    for r in rows:
        fn = Path((r.get('filename') or '').strip()).name
        if not fn:
            continue
        winner = (r.get('winner') or '').strip()
        if not winner:
            continue
        val = to_money64(r.get('company_value'))
        key = fn.lower()
        prev = best.get(key)
        if prev is None or val > prev[2]:
            best[key] = (fn, winner, val, INT64_MIN)
    return best


def write_from_map(entries: Dict[str, Tuple[str, str, int, int]], out_path: Path):
    items = list(entries.values())
    # Deterministic order by filename
    items.sort(key=lambda t: t[0].lower())
    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', VERSION))
        f.write(struct.pack('<I', len(items)))
        for fn, name, val, ts in items:
            write_cstring(f, fn)
            write_cstring(f, name)
            f.write(struct.pack('<q', int(val)))
            f.write(struct.pack('<q', int(ts)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build OpenRCT2 highscores.dat (v2) from RCT1 CSV or CSS0.DAT')
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument('-i', '--input', help='Path to input CSV (filename, name, company_value, winner)')
    src.add_argument('--css0', help='Path to CSS0.DAT to parse directly')
    parser.add_argument('-o', '--output', required=True, help='Path to output highscores.dat')
    parser.add_argument('--merge', action='store_true', help='Merge into existing highscores.dat (keep higher company value per scenario)')
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Load existing map if merge
    existing_map: Dict[str, Tuple[str, str, int, int]] = {}
    if args.merge and out.exists():
        existing_map = load_highscores(out)

    # Build new map from input
    if args.css0:
        rows = rows_from_css0(Path(args.css0))
    else:
        csv_in = Path(args.input)
        with open(csv_in, newline='', encoding='utf-8-sig') as fh:
            rows = list(csv.DictReader(fh))

    new_map = best_map_from_rows(rows)

    if args.merge:
        # Merge: prefer higher company value per filename
        merged = dict(existing_map)
        for k, v in new_map.items():
            prev = merged.get(k)
            if prev is None or v[2] > prev[2]:
                merged[k] = v
        write_from_map(merged, out)
        print(f"highscores.dat merged and written: {out}")
        print(f"Entries: {len(merged)}")
    else:
        # Overwrite with only new entries
        write_from_map(new_map, out)
        print(f"highscores.dat written: {out}")
        print(f"Entries: {len(new_map)}")
