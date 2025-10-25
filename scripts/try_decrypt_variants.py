import struct
from pathlib import Path

MASK = 0xFFFFFFFF
HEX_ADD = 0x39393939
DEC_ADD = 39393939
KEYS = [b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes']


def rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK


def rotr(x, n):
    return ((x >> n) | ((x << (32 - n)) & MASK)) & MASK


def decrypt_bytes(data: bytes, add: int, order: str = 'rotl_then_sub', endian='<'):
    out = bytearray()
    fmt = '<I' if endian == '<' else '>I'
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk)
            break
        (w,) = struct.unpack(fmt, chunk)
        if order == 'rotl_then_sub':
            tmp = rotl(w, 5)
            plain = (tmp - add) & MASK
        elif order == 'sub_then_rotl':
            tmp = (w - add) & MASK
            plain = rotl(tmp, 5)
        elif order == 'rotr_then_sub':
            tmp = rotr(w, 5)
            plain = (tmp - add) & MASK
        else:
            raise ValueError(order)
        out.extend(struct.pack(fmt, plain))
    return bytes(out)


def rle_decompress(data: bytes) -> bytes:
    # data: compressed including trailing checksum DWord - omit last 4 bytes
    if len(data) < 4:
        return b''
    data_body = data[:-4]
    out = bytearray()
    i = 0
    while i < len(data_body):
        b = data_body[i]
        i += 1
        # interpret as signed byte
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


def search_keywords(data: bytes):
    found = {}
    for k in KEYS:
        idx = data.find(k)
        found[k.decode()] = idx
    return found


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    inp = root / 'CSS0.DAT'
    raw = inp.read_bytes()
    variants = []
    combos = [
        ('hex_add', HEX_ADD, 'rotl_then_sub', '<'),
        ('dec_add', DEC_ADD, 'rotl_then_sub', '<'),
        ('hex_add_alt', HEX_ADD, 'sub_then_rotl', '<'),
        ('dec_add_alt', DEC_ADD, 'sub_then_rotl', '<'),
        ('hex_add_be', HEX_ADD, 'rotl_then_sub', '>'),
        ('dec_add_be', DEC_ADD, 'rotl_then_sub', '>'),
    ]
    for name, add, order, endian in combos:
        dec = decrypt_bytes(raw, add, order, endian)
        # write decrypted candidate
        outp = root / f'CSS0.{name}.bin'
        outp.write_bytes(dec)
        # try rle decompress
        try:
            decompr = rle_decompress(dec)
        except Exception as e:
            decompr = b''
        found = search_keywords(decompr)
        print(f'Variant: {name}, add={add}, order={order}, endian={endian}')
        for k, idx in found.items():
            if idx != -1:
                snippet = decompr[max(0, idx-32):idx+64]
                print(f'  FOUND {k} at {idx}, snippet:')
                print(snippet.decode('ascii', errors='replace'))
            else:
                print(f'  not found: {k}')
        print('-' * 60)

    print('Wrote candidate files in', root)
