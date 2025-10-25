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


def decrypt_variation(data: bytes, endian: str, rot: int, op: str, mode: str, add_val: int):
    fmt = '<I' if endian == '<' else '>I'
    out = bytearray()
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            out.extend(chunk)
            break
        (w,) = struct.unpack(fmt, chunk)
        # apply mode
        if mode == 'add':
            w2 = (w - add_val) & MASK  # assume stored cipher; will adjust in ops
        elif mode == 'xor':
            w2 = w ^ add_val
        elif mode == 'none':
            w2 = w
        else:
            w2 = w
        if op == 'rotl_then_sub':
            tmp = rotl(w, rot)
            plain = (tmp - add_val) & MASK
        elif op == 'sub_then_rotl':
            tmp = (w - add_val) & MASK
            plain = rotl(tmp, rot)
        elif op == 'rotr_then_sub':
            tmp = rotr(w, rot)
            plain = (tmp - add_val) & MASK
        elif op == 'xor_then_rotl':
            tmp = (w ^ add_val) & MASK
            plain = rotl(tmp, rot)
        elif op == 'rotl_then_xor':
            tmp = rotl(w, rot)
            plain = tmp ^ add_val
        else:
            # default: do rotl then subtract
            tmp = rotl(w, rot)
            plain = (tmp - add_val) & MASK
        out.extend(struct.pack(fmt, plain))
    return bytes(out)


def search_in(data: bytes):
    hits = {}
    for k in KEYS:
        idx = data.find(k)
        hits[k.decode()] = idx
    return hits


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    inp = root / 'CSS0.DAT'
    raw = inp.read_bytes()
    endians = ['<', '>']
    ops = ['rotl_then_sub', 'sub_then_rotl', 'rotr_then_sub', 'xor_then_rotl', 'rotl_then_xor']
    adds = [('hex', HEX_ADD), ('dec', DEC_ADD)]

    found_any = False
    for endian in endians:
        for op in ops:
            for name, add in adds:
                for rot in range(0, 32):
                    dec = decrypt_variation(raw, endian, rot, op, 'add', add)
                    # search raw
                    hits_raw = search_in(dec)
                    # attempt rle
                    try:
                        decompr = rle_decompress(dec)
                    except Exception:
                        decompr = b''
                    hits_rle = search_in(decompr)
                    any_raw = [k for k,v in hits_raw.items() if v!=-1]
                    any_rle = [k for k,v in hits_rle.items() if v!=-1]
                    if any_raw or any_rle:
                        found_any = True
                        print('MATCH: endian=%s op=%s add=%s rot=%d raw_hits=%s rle_hits=%s' % (endian, op, name, rot, any_raw, any_rle))
                        # write outputs
                        outp = root / f'candidate_{endian}_{op}_{name}_rot{rot}.bin'
                        outp.write_bytes(dec)
                        outp2 = root / f'candidate_{endian}_{op}_{name}_rot{rot}_rle.bin'
                        outp2.write_bytes(decompr)
    if not found_any:
        print('No matches found')
    else:
        print('Candidates written to', root)
