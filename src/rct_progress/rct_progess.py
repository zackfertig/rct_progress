import struct

def read_rct_progress(fname):
    with open(fname, 'rb') as f:
        filecontents = f.read()
    bfilecontents = struct.unpack("B"*len(filecontents), filecontents)  # Read as bytes
    print(f"Read {len(bfilecontents)} bytes from {fname}")
    data = bfilecontents[:-4]
    data = bytearray(data)
    
    checksum = struct.unpack("L", filecontents[-4:])[0]
    
    isvalid, calculated_checksum = verify_checksum(data, checksum)
    if not isvalid:
        print("Checksum invalid")
        raise Exception(f"Checksum invalid for {fname}. Expected {checksum}, calculated {calculated_checksum}.")
    else:
        print("Checksum valid")
    
    data = decrypt_data(data)
    data = rle_decode(data)
    
    print(f"Decoded into {len(data)} bytes")
    with open(fname + ".dec", 'wb') as f:
        f.write(data)
    return data

def decrypt_data(data):
    # data is a bytearray or bytes-like; work on a copy or return a new bytearray
    orig_len = len(data)
    padded = bytearray(data)
    if orig_len % 4 != 0:
        padded.extend(b'\x00' * (4 - (orig_len % 4)))

    offset = 0x39393939
    decrypted = bytearray()
    for i in range(0, len(padded), 4):
        # read 4 bytes as unsigned 32-bit little-endian (padded ensures 4 bytes available)
        dword = int.from_bytes(padded[i:i+4], byteorder='little', signed=False) & 0xFFFFFFFF

        # rotate within 32 bits and subtract offset, always keeping 32-bit unsigned
        dword = rotate_left(dword, 5, 32) & 0xFFFFFFFF
        dword = (dword - offset) & 0xFFFFFFFF
        decrypted.extend(dword.to_bytes(4, byteorder='little', signed=False))

    # return only the original number of bytes (drop padding)
    return decrypted[:orig_len]


def rotate_left(value, shift, size):
    shift %= size
    return ((value << shift) | (value >> (size - shift))) & ((1 << size) - 1)

def rotate_right(value, shift, size):
    shift %= size
    return ((value >> shift) | (value << (size - shift))) & ((1 << size) - 1)

def verify_checksum(data, expected_checksum):
    total = 0 #struct.pack("L", 0)[0]
    for byte in data:
        val = (total + byte) % 256
        total = ((total & 0xFFFFFF00) | (val & 0x000000FF)) % 2**32
        total = rotate_left(total, 3, 32) % 2**32
    calculated_checksum = ((total & 0xFFFFFFFF) + 120001) % 2**32
    #print(f"Calculated checksum: {calculated_checksum}")
    #print(f"Expected checksum: {expected_checksum}")
    return calculated_checksum == expected_checksum, calculated_checksum

def rle_decode(data):
    decoded = bytearray()
    i = 0
    while i < len(data):
        ctrl = data[i]
        i += 1
        if ctrl & 0x80:  # High bit set indicates a run
            run_length = -(ctrl & 0x7F) % 128 + 1
            if i >= len(data):
                pass
                #raise ValueError("RLE data ends unexpectedly while reading run value")
            run_value = data[i]
            decoded.extend([run_value] * run_length)
            i += 1
        else:
            literal_length = (ctrl & 0x7F) % 128 + 1
            if i + literal_length > len(data):
                pass
                #raise ValueError("RLE data ends unexpectedly while reading literal bytes")
            decoded.extend(data[i:i+literal_length])
            i += literal_length
    #decodeddata = struct.pack("B"*len(decoded), decoded)
    return decoded


def main():
    print("Hello from rct_progress!")
    fname = "CSS0.DAT"
    testbytes = bytearray.fromhex("00 47 FF 6F 05 64 20 6A 6F 62 21")
    result = rle_decode(testbytes)
    print(f"Test bytes: {result}")
    data = read_rct_progress(fname)

if __name__ == "__main__":
    main()

    