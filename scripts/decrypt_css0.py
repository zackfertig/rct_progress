import sys
import struct
from pathlib import Path

MAGIC_ADD = 0x39393939
MASK32 = 0xFFFFFFFF

def rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32

def rotr32(x, n):
    return ((x >> n) | ((x << (32 - n)) & MASK32)) & MASK32

def decrypt_stream(input_path: Path, output_path: Path, endian='<'):
    """Decrypt file using specified endian and default algorithm.

    The normal (default) algorithm reverses: encrypted = ROTR32(plain + ADD, 5)
    so decryption is: tmp = ROTL32(encrypted, 5); plain = tmp - ADD
    """
    read_fmt = endian + 'I'
    with input_path.open('rb') as f_in, output_path.open('wb') as f_out:
        while True:
            chunk = f_in.read(4)
            if not chunk:
                break
            if len(chunk) < 4:
                # trailing bytes: copy as-is
                f_out.write(chunk)
                break
            (cipherword,) = struct.unpack(read_fmt, chunk)
            tmp = rotl32(cipherword, 5)                 # reverse ROTR( ,5)
            plainword = (tmp - MAGIC_ADD) & MASK32      # reverse add
            f_out.write(struct.pack(read_fmt, plainword))


def decrypt_stream_alt(input_path: Path, output_path: Path, endian='<'):
    """Alternative decryption: subtract first, then rotate left.

    Some implementations accidentally do: encrypted = ROTR32(plain,5) + ADD
    which would require: tmp = (cipher - ADD) ; plain = ROTL32(tmp,5)
    This function helps test that variant.
    """
    read_fmt = endian + 'I'
    with input_path.open('rb') as f_in, output_path.open('wb') as f_out:
        while True:
            chunk = f_in.read(4)
            if not chunk:
                break
            if len(chunk) < 4:
                f_out.write(chunk)
                break
            (cipherword,) = struct.unpack(read_fmt, chunk)
            tmp = (cipherword - MAGIC_ADD) & MASK32
            plainword = rotl32(tmp, 5)
            f_out.write(struct.pack(read_fmt, plainword))

def hexdump_sample(path: Path, offset=0, length=64):
    with path.open('rb') as f:
        f.seek(offset)
        data = f.read(length)
    hexstr = ' '.join(f'{b:02X}' for b in data)
    try:
        txt = data.decode('ascii', errors='replace')
    except Exception:
        txt = ''
    print(f'Offset {offset:#x} ({length} bytes):')
    print(hexstr)
    print(txt)

def main():
    if len(sys.argv) < 3:
        print("Usage: python decrypt_css0.py input.bin output.bin [--be]")
        return
    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2])
    endian = '>' if '--be' in sys.argv else '<'
    decrypt_stream(inp, outp, endian)
    print("Wrote", outp)
    # also write alternative decryption for comparison
    alt_out = outp.with_name(outp.stem + '_alt' + outp.suffix)
    decrypt_stream_alt(inp, alt_out, endian)
    print("Wrote alternative output:", alt_out)
    print("Decrypted samples (default):")
    hexdump_sample(outp, 0x0000, 64)
    hexdump_sample(outp, 0x0800, 64)
    print("Decrypted samples (alternative):")
    hexdump_sample(alt_out, 0x0000, 64)
    hexdump_sample(alt_out, 0x0800, 64)

if __name__ == '__main__':
    main()