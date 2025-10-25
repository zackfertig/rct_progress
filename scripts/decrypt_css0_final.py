import struct
from pathlib import Path

MAGIC_ADD = 0x39393939
MASK32 = 0xFFFFFFFF

def rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32

def decrypt_full(data: bytes, endian='<'):
    fmt = '<I' if endian == '<' else '>I'
    out = bytearray()
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk)
            break
        (w,) = struct.unpack(fmt, chunk)
        tmp = rotl32(w, 5)
        plain = (tmp - MAGIC_ADD) & MASK32
        out.extend(struct.pack(fmt, plain))
    return bytes(out)

def rle_decompress(data: bytes) -> bytes:
    if len(data) < 4:
        return b''
    body = data[:-4]
    out = bytearray()
    i = 0
    while i < len(body):
        b = body[i]; i += 1
        sb = b if b < 128 else b - 256
        if sb >= 0:
            cnt = sb + 1
            out.extend(body[i:i+cnt]); i += cnt
        else:
            cnt = 1 - sb
            if i >= len(body): break
            val = body[i]; i += 1
            out.extend(bytes([val]) * cnt)
    return bytes(out)

def hexdump(data: bytes, off=0, length=64):
    s = data[off:off+length]
    print(f'Offset {hex(off)}:')
    print(' '.join(f'{b:02X}' for b in s))
    print(s.decode('ascii', errors='replace'))

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    inp = root / 'CSS0.DAT'
    raw = inp.read_bytes()
    # try little endian first
    dec_le = decrypt_full(raw, '<')
    (root / 'CSS0.decrypted.le.bin').write_bytes(dec_le)
    decompr_le = rle_decompress(dec_le)
    (root / 'CSS0.decompressed.le.bin').write_bytes(decompr_le)
    print('Little-endian: decompressed size', len(decompr_le))
    hexdump(decompr_le, 0x0000, 64)
    hexdump(decompr_le, 0x0800, 64)
    for name in (b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes'):
        print(name.decode(), '->', decompr_le.find(name))

    # try big endian
    dec_be = decrypt_full(raw, '>')
    (root / 'CSS0.decrypted.be.bin').write_bytes(dec_be)
    decompr_be = rle_decompress(dec_be)
    (root / 'CSS0.decompressed.be.bin').write_bytes(decompr_be)
    print('Big-endian: decompressed size', len(decompr_be))
    hexdump(decompr_be, 0x0000, 64)
    hexdump(decompr_be, 0x0800, 64)
    for name in (b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes'):
        print(name.decode(), '->', decompr_be.find(name))
