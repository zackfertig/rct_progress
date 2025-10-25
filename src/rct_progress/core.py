"""Core functionality for rct_progress: RLE decompress, decrypt, checksum and parsing.

This module implements the low-level operations used to decode the
CSS0.DAT archive used by RollerCoaster Tycoon progress/scenario files.

Functions are intentionally small and pure where possible so they are
easy to test.
"""
from pathlib import Path
import struct
import csv
import logging
from typing import List, Tuple

MAGIC_ADD = 0x39393939
MASK32 = 0xFFFFFFFF


def rotl32(x: int, n: int) -> int:
    """Rotate a 32-bit integer left by n bits.

    Args:
        x: input integer (will be masked to 32 bits).
        n: number of bits to rotate left.

    Returns:
        Rotated 32-bit integer.
    """
    return ((x << n) | (x >> (32 - n))) & MASK32


def rle_decompress(data: bytes) -> bytes:
    """Decompress RCT/TD4-style RLE data.

    The compressed format stores a stream of control bytes followed by
    literal or repeated bytes. The final 4 bytes of the provided
    buffer are expected to be a checksum and are ignored by this
    function (they should be verified prior to calling).

    Args:
        data: compressed payload including trailing 4-byte checksum.

    Returns:
        The decompressed bytes.
    """
    if len(data) < 4:
        return b''
    body = data[:-4]
    out = bytearray()
    i = 0
    while i < len(body):
        b = body[i]
        i += 1
        # signed interpretation of control byte
        sb = b if b < 128 else b - 256
        if sb >= 0:
            # sb >= 0 -> copy next (sb + 1) literal bytes
            cnt = sb + 1
            out.extend(body[i:i+cnt])
            i += cnt
        else:
            # sb < 0 -> repeat next byte (-sb + 1) times
            cnt = 1 - sb
            if i >= len(body):
                break
            val = body[i]; i += 1
            out.extend(bytes([val]) * cnt)
    return bytes(out)


def decrypt_dwords_le(data: bytes) -> bytes:
    """Decrypt a byte sequence interpreted as little-endian 32-bit DWords.

    The reverse operation implemented here is the inverse of the
    original encryption: each 32-bit word is rotated left 5 bits and
    then the constant MAGIC_ADD is subtracted modulo 2**32.

    Args:
        data: bytes to decrypt (length does not need to be a multiple of 4)

    Returns:
        Decrypted bytes with the same length as the input.
    """
    fmt = '<I'
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


def verify_checksum(data: bytes, expected_checksum: int) -> Tuple[bool, int]:
    """Verify compressed-data checksum.

    The checksum algorithm is derived from the game's format: iterate
    each byte, add it to the low byte of a running 32-bit total, rotate
    the total left by 3 bits, and at the end add 120001.

    Args:
        data: compressed data excluding the trailing 4-byte checksum.
        expected_checksum: expected 32-bit checksum value.

    Returns:
        Tuple (is_valid, calculated_checksum).
    """
    total = 0
    for byte in data:
        val = (total + byte) % 256
        total = ((total & 0xFFFFFF00) | (val & 0x000000FF)) % (1 << 32)
        total = rotl32(total, 3) % (1 << 32)
    calculated_checksum = ((total & 0xFFFFFFFF) + 120001) % (1 << 32)
    return (calculated_checksum == expected_checksum, calculated_checksum)


def read_fixed_strings(data: bytes, offset: int, count: int, size: int) -> List[str]:
    """Read fixed-size, null-terminated strings from a byte buffer.

    Args:
        data: source bytes.
        offset: byte offset to start reading.
        count: maximum number of entries to read.
        size: size of each fixed block in bytes.

    Returns:
        List of decoded strings (latin1, replacement for invalid bytes).
    """
    items: List[str] = []
    for i in range(count):
        start = offset + i*size
        if start >= len(data):
            break
        block = data[start: start+size]
        s = block.split(b'\x00',1)[0].decode('latin1', errors='replace')
        items.append(s)
    return items


def read_dwords_le(data: bytes, offset: int, count: int) -> List[int]:
    """Read little-endian 32-bit words from a byte buffer.

    Args:
        data: source bytes.
        offset: starting offset in bytes.
        count: maximum number of DWords to read.

    Returns:
        List of integers.
    """
    items: List[int] = []
    for i in range(count):
        off = offset + i*4
        if off+4 > len(data):
            break
        items.append(struct.unpack_from('<I', data, off)[0])
    return items


def parse_and_write(decomp: bytes, decrypted: bytes, out_csv: Path) -> List[dict]:
    """Parse tables from the decrypted data and write to CSV.

    The parser reads several tables at fixed offsets found by
    inspecting the game's data layout:
      - filenames at 0x0000 (16 bytes each)
      - scenario names at 0x0800 (64 bytes each)
      - company values at 0x2800 (DWords)
      - winners at 0x2A00 (32 bytes each)

    The function is defensive and computes maximum counts based on
    available buffer size so it won't raise on truncated inputs.

    Args:
        decomp: the decompressed byte stream (used only for diagnostics)
        decrypted: the decrypted byte stream to parse tables from
        out_csv: path to write the resulting CSV

    Returns:
        List of row dictionaries that were written to CSV.
    """
    total = len(decrypted)
    max_files = max(0, (total - 0x0000) // 16)
    max_files = min(max_files, 128)
    files = read_fixed_strings(decrypted, 0x0000, max_files, 16)
    max_names = 0
    if len(decrypted) > 0x0800:
        max_names = min(128, (len(decrypted) - 0x0800) // 64)
    names = read_fixed_strings(decrypted, 0x0800, max_names, 64)
    comps = []
    if len(decrypted) > 0x2800:
        max_comp = min(128, (len(decrypted) - 0x2800) // 4)
        comps = read_dwords_le(decrypted, 0x2800, max_comp)
    wins = []
    if len(decrypted) > 0x2A00:
        max_w = min(128, (len(decrypted) - 0x2A00) // 32)
        wins = read_fixed_strings(decrypted, 0x2A00, max_w, 32)

    rows: List[dict] = []
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


def process_file(input_path: Path, out_csv: Path, verbose: bool = False) -> List[dict]:
    """Process a `CSS0.DAT` file end-to-end.

    Steps performed:
      1. Validate checksum on compressed input (last 4 bytes)
      2. RLE-decompress the compressed body
      3. Decrypt the decompressed DWords
      4. Parse tables and write CSV

    Args:
        input_path: Path to the compressed CSS0.DAT file.
        out_csv: Path to the CSV file to write.
        verbose: When True, write intermediate binary files next to the input.

    Returns:
        The list of parsed rows written to CSV.
    """
    logger = logging.getLogger(__name__)
    raw = input_path.read_bytes()
    if len(raw) < 4:
        raise ValueError('Input file too small to contain checksum')
    expected_checksum = struct.unpack_from('<I', raw, len(raw)-4)[0]
    compressed_body = raw[:-4]
    ok, calc = verify_checksum(compressed_body, expected_checksum)
    if not ok:
        raise ValueError(f'Checksum mismatch: expected {expected_checksum}, calculated {calc}')
    if verbose:
        logger.info('Checksum valid: %d', expected_checksum)
    decompr_raw = rle_decompress(raw)
    if verbose:
        (input_path.parent / 'CSS0.decompressed.raw.bin').write_bytes(decompr_raw)
        logger.info('Wrote %s size %d', input_path.parent / 'CSS0.decompressed.raw.bin', len(decompr_raw))
    decrypted = decrypt_dwords_le(decompr_raw)
    if verbose:
        (input_path.parent / 'CSS0.decrypted.bin').write_bytes(decrypted)
        logger.info('Wrote %s size %d', input_path.parent / 'CSS0.decrypted.bin', len(decrypted))
    rows = parse_and_write(decompr_raw, decrypted, out_csv)
    return rows
