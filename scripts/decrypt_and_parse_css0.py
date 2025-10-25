"""Decompress-then-decrypt the raw CSS0.DAT, parse fields and write csv.

Produces:
- CSS0.decompressed.raw.bin  (raw RLE-decompressed bytes)
- CSS0.decrypted.bin         (decrypted DWord stream)
- css0_parsed.csv            (parsed table rows found)

Usage: python decrypt_and_parse_css0.py
"""
from pathlib import Path
import struct
import csv

MAGIC_ADD = 0x39393939
MASK32 = 0xFFFFFFFF

def rle_decompress(data: bytes) -> bytes:
    if len(data) < 4:
        return b''
    body = data[:-4]
    out = bytearray()
    i = 0
    while i < len(body):
        b = body[i]
        i += 1
        sb = b if b < 128 else b - 256
        if sb >= 0:
            cnt = sb + 1
            out.extend(body[i:i+cnt])
            i += cnt
        else:
            cnt = 1 - sb
            if i >= len(body): break
            val = body[i]; i += 1
            out.extend(bytes([val]) * cnt)
    return bytes(out)

def rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32

def decrypt_dwords_le(data: bytes) -> bytes:
    fmt = '<I'
    out = bytearray()
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk); break
        (w,) = struct.unpack(fmt, chunk)
        tmp = rotl32(w, 5)
        plain = (tmp - MAGIC_ADD) & MASK32
        out.extend(struct.pack(fmt, plain))
    return bytes(out)

def read_fixed_strings(data: bytes, offset: int, count: int, size: int):
    items = []
    for i in range(count):
        start = offset + i*size
        if start >= len(data):
            break
        block = data[start: start+size]
        s = block.split(b'\x00',1)[0].decode('latin1', errors='replace')
        items.append(s)
    return items

def read_dwords_le(data: bytes, offset: int, count: int):
    items = []
    for i in range(count):
        off = offset + i*4
        if off+4 > len(data): break
        items.append(struct.unpack_from('<I', data, off)[0])
    return items

def parse_and_write(decomp: bytes, decrypted: bytes, out_csv: Path):
    # parse available tables but don't assume full length; compute counts by available bytes
    total = len(decrypted)
    # filename table at 0x0000 entries of 16 bytes
    max_files = max(0, (total - 0x0000) // 16)
    max_files = min(max_files, 128)
    files = read_fixed_strings(decrypted, 0x0000, max_files, 16)
    # scenario names at 0x0800 entries of 64 bytes
    max_names = 0
    if len(decrypted) > 0x0800:
        max_names = min(128, (len(decrypted) - 0x0800) // 64)
    names = read_fixed_strings(decrypted, 0x0800, max_names, 64)
    # company values as DWords at 0x2800
    comps = []
    if len(decrypted) > 0x2800:
        max_comp = min(128, (len(decrypted) - 0x2800) // 4)
        comps = read_dwords_le(decrypted, 0x2800, max_comp)
    # winners at 0x2A00 entries 32 bytes
    wins = []
    if len(decrypted) > 0x2A00:
        max_w = min(128, (len(decrypted) - 0x2A00) // 32)
        wins = read_fixed_strings(decrypted, 0x2A00, max_w, 32)

    rows = []
    count = max(len(files), len(names), len(comps), len(wins))
    for i in range(count):
        rows.append({
            'index': i,
            'filename': files[i] if i < len(files) else '',
            'name': names[i] if i < len(names) else '',
            'company_value': comps[i] if i < len(comps) else '',
            'winner': wins[i] if i < len(wins) else '',
        })

    with out_csv.open('w', newline='', encoding='utf8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['index','filename','name','company_value','winner'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return rows

def main():
    root = Path(__file__).resolve().parents[1]
    raw = (root / 'CSS0.DAT').read_bytes()
    # decompress raw (omit last 4 bytes of raw as checksum)
    decompr_raw = rle_decompress(raw)
    (root / 'CSS0.decompressed.raw.bin').write_bytes(decompr_raw)
    print('Wrote CSS0.decompressed.raw.bin size', len(decompr_raw))
    # decrypt decompressed bytes (little-endian assumption)
    decrypted = decrypt_dwords_le(decompr_raw)
    (root / 'CSS0.decrypted.bin').write_bytes(decrypted)
    print('Wrote CSS0.decrypted.bin size', len(decrypted))
    # parse and write csv
    outcsv = root / 'css0_parsed.csv'
    rows = parse_and_write(decompr_raw, decrypted, outcsv)
    print('Wrote', outcsv, 'rows', len(rows))

    # quick print of found keywords and key offsets
    data = decrypted
    for name in (b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes'):
        pos = data.find(name)
        print(name.decode(), '->', pos)

if __name__ == '__main__':
    main()
