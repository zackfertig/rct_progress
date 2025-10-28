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
    # money64: internal scale x10
    return int(v * 10)


def build(csv_path: Path, out_path: Path):
    with open(csv_path, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))

    # Only write entries that have a filename and a non-empty winner
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


if __name__ == '__main__':
    csv_in = Path(r'c:\Users\Krabs\repos\rct_progress\outdir\css0_parsed_split.csv')
    out = csv_in.with_name('highscores.dat')
    build(csv_in, out)
