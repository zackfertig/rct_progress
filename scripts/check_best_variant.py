import struct
from pathlib import Path

MASK = 0xFFFFFFFF
DEC_ADD = 39393939
KEYS = [b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes']


def rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK


def rle_decompress(data: bytes) -> bytes:
    if len(data) < 4:
        return b''
    data_body = data[:-4]
    out = bytearray()
    i = 0
    while i < len(data_body):
        b = data_body[i]
        i += 1
        sb = b if b < 128 else b - 256
        if sb >= 0:
            count = sb + 1
            out.extend(data_body[i:i+count])
            i += count
        else:
            count = 1 - sb
            if i >= len(data_body):
                break
            val = data_body[i]
            i += 1
            out.extend(bytes([val]) * count)
    return bytes(out)


def apply_variant(raw: bytes, endian: str, add: int, rot: int):
    fmt = '<I' if endian == '<' else '>I'
    out = bytearray()
    for i in range(0, len(raw), 4):
        chunk = raw[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk)
            break
        (w,) = struct.unpack(fmt, chunk)
        tmp = (w ^ add) & MASK
        plain = rotl(tmp, rot)
        out.extend(struct.pack(fmt, plain))
    return bytes(out)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    raw = (root / 'CSS0.DAT').read_bytes()
    for endian in ('<','>'):
        dec = apply_variant(raw, endian, DEC_ADD, 23)
        decom = rle_decompress(dec)
        print('Endian', endian, 'decompressed size', len(decom))
        for k in KEYS:
            idx = decom.find(k)
            print('  ', k.decode(), '->', idx)
            if idx != -1:
                start = max(0, idx-40)
                print(decom[start:idx+80].decode('ascii', errors='replace'))
        print('-'*60)
