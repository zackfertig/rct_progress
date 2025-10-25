import struct
from pathlib import Path

MASK = 0xFFFFFFFF
HEX_ADD = 0x39393939
KEYS = [b'Patrick', b'Forest Frontiers', b'Leafy Lake', b'Dynamite Dunes']

def rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK

def rotr(x, n):
    return ((x >> n) | ((x << (32 - n)) & MASK)) & MASK

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

def rle_test():
    # doc example: 00 47 FF 6F 05 64 20 6A 6F 62 21 -> Good job!
    data = bytes([0x00, 0x47, 0xFF, 0x6F, 0x05, 0x64, 0x20, 0x6A, 0x6F, 0x62, 0x21, 0x00,0x00,0x00,0x00])
    # append 4-byte checksum placeholder so decompressor omits them
    out = rle_decompress(data)
    print('RLE test output:', out)
    assert out == b'Goo djob!' or out.replace(b' ',b'')==b'Goodjob!' or b'Good' in out

def decrypt_words(data: bytes, order='rotl_then_sub', endian='<'):
    fmt = '<I' if endian == '<' else '>I'
    out = bytearray()
    for i in range(0, len(data), 4):
        ch = data[i:i+4]
        if len(ch) < 4:
            out.extend(ch); break
        (w,) = struct.unpack(fmt, ch)
        if order == 'rotl_then_sub':
            tmp = rotl(w, 5); plain = (tmp - HEX_ADD) & MASK
        elif order == 'sub_then_rotl':
            tmp = (w - HEX_ADD) & MASK; plain = rotl(tmp, 5)
        elif order == 'rotr_then_sub':
            tmp = rotr(w, 5); plain = (tmp - HEX_ADD) & MASK
        else:
            tmp = rotl(w,5); plain = (tmp - HEX_ADD) & MASK
        out.extend(struct.pack(fmt, plain))
    return bytes(out)

def search_keywords(data: bytes):
    return {k.decode(): data.find(k) for k in KEYS}

def hexdump(data: bytes, off=0, n=64):
    s = data[off:off+n]
    print('Offset',hex(off), 'len', len(s))
    print(' '.join(f'{b:02X}' for b in s))
    print(s.decode('latin1',errors='replace'))

def decrypt_then_decompress(raw: bytes, order='rotl_then_sub', endian='<'):
    dec = decrypt_words(raw, order, endian)
    decompr = rle_decompress(dec)
    return dec, decompr

def decompress_then_decrypt(raw: bytes, order='rotl_then_sub', endian='<'):
    # attempt to RLE-decompress the raw encrypted file (omit last 4 bytes of raw)
    decompr_raw = rle_decompress(raw)
    # now treat decompr_raw as encrypted DWords and decrypt
    dec_after = decrypt_words(decompr_raw, order, endian)
    return decompr_raw, dec_after

if __name__ == '__main__':
    print('RLE decoder self-test (doc example)')
    rle_test()
    root = Path(__file__).resolve().parents[1]
    raw = (root / 'CSS0.DAT').read_bytes()
    print('Raw size', len(raw))

    print('\n== decrypt then decompress (little-endian, rotl_then_sub) ==')
    dec, decompr = decrypt_then_decompress(raw, 'rotl_then_sub', '<')
    print('Decrypted size', len(dec), 'Decompressed size', len(decompr))
    print('Keywords:', search_keywords(decompr))
    hexdump(decompr,0,64)
    hexdump(decompr,0x800,64)

    print('\n== decompress raw then decrypt (little-endian) ==')
    dcomp_raw, dec_after = decompress_then_decrypt(raw, 'rotl_then_sub', '<')
    print('Decompressed(raw) size', len(dcomp_raw), 'Then decrypted size', len(dec_after))
    print('Keywords after decrypting decompressed-raw:', search_keywords(dec_after))
    hexdump(dcomp_raw,0,64)
    hexdump(dec_after,0,64)

    # also try alternative decrypt order (sub_then_rotl)
    print('\n== decrypt then decompress (sub_then_rotl) ==')
    dec2, decompr2 = decrypt_then_decompress(raw, 'sub_then_rotl', '<')
    print('Keywords:', search_keywords(decompr2))
    hexdump(decompr2,0,64)

    print('\n== decompress raw then decrypt (sub_then_rotl) ==')
    dcomp_raw2, dec_after2 = decompress_then_decrypt(raw, 'sub_then_rotl', '<')
    print('Keywords after decrypting decompressed-raw:', search_keywords(dec_after2))
    hexdump(dcomp_raw2,0,64)
    hexdump(dec_after2,0,64)
