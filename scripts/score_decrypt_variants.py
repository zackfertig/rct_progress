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


def byteswap_word(w):
    return struct.unpack('<I', struct.pack('>I', w))[0]


def decrypt_and_score(raw: bytes, endian: str, op: str, add: int, rot: int, swap: bool, negate: bool):
    fmt = '<I' if endian == '<' else '>I'
    out = bytearray()
    for i in range(0, len(raw), 4):
        chunk = raw[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk)
            break
        (w,) = struct.unpack(fmt, chunk)
        if op == 'rotl_then_sub':
            tmp = rotl(w, rot)
            plain = (tmp - add) & MASK
        elif op == 'sub_then_rotl':
            tmp = (w - add) & MASK
            plain = rotl(tmp, rot)
        elif op == 'rotr_then_sub':
            tmp = rotr(w, rot)
            plain = (tmp - add) & MASK
        elif op == 'xor_then_rotl':
            tmp = (w ^ add) & MASK
            plain = rotl(tmp, rot)
        elif op == 'rotl_then_xor':
            tmp = rotl(w, rot)
            plain = tmp ^ add
        else:
            tmp = rotl(w, rot)
            plain = (tmp - add) & MASK
        if negate:
            plain = (~plain) & MASK
        if swap:
            plain = byteswap_word(plain)
        out.extend(struct.pack(fmt, plain))
    # attempt rle
    try:
        decompr = rle_decompress(bytes(out))
    except Exception:
        decompr = b''
    # score printable fraction
    if len(decompr) == 0:
        score = 0.0
    else:
        printable = sum(1 for b in decompr if 32 <= b < 127 or b in (9,10,13))
        score = printable / len(decompr)
    # check for keywords
    hits = {k.decode(): decompr.find(k) for k in KEYS}
    return score, hits, decompr


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    inp = root / 'CSS0.DAT'
    raw = inp.read_bytes()
    endians = ['<', '>']
    ops = ['rotl_then_sub', 'sub_then_rotl', 'rotr_then_sub', 'xor_then_rotl', 'rotl_then_xor']
    adds = [('hex', HEX_ADD), ('dec', DEC_ADD)]
    results = []
    for endian in endians:
        for op in ops:
            for name, add in adds:
                for rot in range(0, 32):
                    for swap in (False, True):
                        for negate in (False, True):
                            score, hits, decompr = decrypt_and_score(raw, endian, op, add, rot, swap, negate)
                            results.append((score, endian, op, name, add, rot, swap, negate, hits))
    results.sort(reverse=True, key=lambda r: r[0])
    print('Top 10 candidates by printable ASCII fraction after RLE decompress:')
    for r in results[:10]:
        score, endian, op, name, add, rot, swap, negate, hits = r
        print(f'score={score:.4f} endian={endian} op={op} add={name} rot={rot} swap={swap} negate={negate} hits={hits}')
    # also print any with keyword hits
    print('\nAny keyword hits:')
    for r in results:
        score, endian, op, name, add, rot, swap, negate, hits = r
        for k,v in hits.items():
            if v != -1:
                print(f'keyword {k} found: score={score:.4f} endian={endian} op={op} add={name} rot={rot} swap={swap} negate={negate} pos={v}')
    print('Done')
