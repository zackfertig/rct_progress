from pathlib import Path
import struct
import re

# Layout (from your description)
# 0x0000..0x07FF : 128 entries * 16 bytes = scenario filenames
# 0x0800..0x27FF : 128 entries * 64 bytes = scenario names
# 0x2800..0x29FF : 128 DWORDs = company value
# 0x2A00..0x39FF : 128 entries * 32 bytes = winner name
# 0x3A00 : number of scenarios (1 byte)
# 0x3A01 : flag (1 byte)
# 0x3A02..3 : creation time parts (2 bytes?)
# 0x3A04..0x3A07 : low DWord of sum of file sizes
# 0x3A08..0x3A0B : high DWord of sum of file sizes
# 0x3A0C..0x3A1B : 128 bit flags (16 bytes)

KEYS = ['patrick','forest','leafy','dynamite','dundee','mega']


def read_fixed_strings(data: bytes, offset: int, count: int, size: int):
    items = []
    for i in range(count):
        s = data[offset + i*size: offset + (i+1)*size]
        # trim at first 0
        try:
            s0 = s.split(b'\x00', 1)[0].decode('latin1')
        except Exception:
            s0 = ''.join(chr(b) if 32<=b<127 else '.' for b in s)
        items.append(s0)
    return items


def read_dwords(data: bytes, offset: int, count: int, endian='<'):
    fmt = '<I' if endian=='<' else '>I'
    items = []
    for i in range(count):
        off = offset + i*4
        if off+4 > len(data):
            items.append(None)
        else:
            items.append(struct.unpack_from(fmt, data, off)[0])
    return items


def parse_decompressed(path: Path):
    data = path.read_bytes()
    print('file size', len(data))
    # ensure enough length
    needed = 0x3A1C
    if len(data) < needed:
        print('Warning: decompressed length < expected header (0x3A1C)')

    names_files = read_fixed_strings(data, 0x0000, 128, 16)
    names_scen = read_fixed_strings(data, 0x0800, 128, 64)
    comp_values = read_dwords(data, 0x2800, 128, '<')
    winners = read_fixed_strings(data, 0x2A00, 128, 32)

    # read number of scenarios (byte)
    num_scen = data[0x3A00] if len(data) > 0x3A00 else None
    flag = data[0x3A01] if len(data) > 0x3A01 else None
    low_sum = struct.unpack_from('<I', data, 0x3A04)[0] if len(data) > 0x3A07 else None
    high_sum = struct.unpack_from('<I', data, 0x3A08)[0] if len(data) > 0x3A0B else None

    print('num_scen', num_scen, 'flag', flag, 'low_sum', low_sum, 'high_sum', high_sum)

    # Print the first few scenario names
    print('\nFirst 16 scenarios (index : file -> name -> company -> winner):')
    for i in range(16):
        f = names_files[i]
        n = names_scen[i]
        cv = comp_values[i]
        w = winners[i]
        print(f'{i:03d}: {f!r} -> {n!r} -> {cv!r} -> {w!r}')

    # search for partial matches case-insensitive in scenario names and winners
    print('\nPartial keyword matches in scenario names and winners:')
    lowered = data.lower()
    for k in KEYS:
        hits = []
        # naive search in whole decompressed data
        idx = lowered.find(k.encode('latin1'))
        while idx != -1:
            start = max(0, idx-40)
            snippet = data[start: idx+80]
            try:
                txt = snippet.decode('latin1', errors='replace')
            except Exception:
                txt = repr(snippet)
            hits.append((idx, txt))
            idx = lowered.find(k.encode('latin1'), idx+1)
        if hits:
            print(f"Keyword '{k}' found {len(hits)} times")
            for pos, snip in hits[:10]:
                print('  pos', pos)
                print('   ', snip)
        else:
            print(f"Keyword '{k}' not found")

    return {
        'files': names_files,
        'names': names_scen,
        'company_values': comp_values,
        'winners': winners,
        'num_scen': num_scen,
    }


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    decompr = root / 'CSS0.decompressed.le.bin'
    if not decompr.exists():
        print('Decompressed file not found - run decrypt first')
    else:
        res = parse_decompressed(decompr)
        # optionally write CSV summary
        out = root / 'css0_parsed.csv'
        with out.open('w', encoding='utf8') as fh:
            fh.write('index,filename,name,company_value,winner\n')
            for i in range(128):
                fh.write(f'{i},{res["files"][i]},{res["names"][i]},{res["company_values"][i]},{res["winners"][i]}\n')
        print('Wrote', out)
