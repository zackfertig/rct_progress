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
        f.write(struct.pack("B"*len(data), *data))
    return data

def decrypt_data(data):
    #finalbytes = bytearray.fromhex('39393939')
    #print(f"Data length modulo 4: {len(data)%4}")
    datac = data
    if len(datac)%4 != 0:
        datac.extend(bytearray(4 - (len(datac)%4)))
    #print(f"Data length after adding final bytes: {len(datac)}")
    #print(f"Data length modulo 4: {len(datac)%4}")
    dworddata = memoryview(datac).cast('I')
    decrypted = bytearray()
    for i in range(len(dworddata)):
        #decrypted_dword = rotate_right(dworddata[i]+0x39393939, 5, 32)
        decrypted_dword = rotate_left(dworddata[i], 5, 32)
        decrypted_dword = (decrypted_dword-0x39393939) % 2**32
        decrypted.extend(struct.pack("L", decrypted_dword))
    # Trim any added bytes
    data[:] = decrypted[:len(data)]
    return data


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
        byte = data[i]
        if byte & 0x80:  # High bit set indicates a run
            run_length = (byte & 0x7F) + 1
            i += 1
            run_value = data[i]
            decoded.extend([run_value] * run_length)
        else:
            literal_length = (byte & 0x7F) + 1
            i += 1
            decoded.extend(data[i:i+literal_length])
            i += literal_length - 1
        i += 1
    #decodeddata = struct.pack("B"*len(decoded), decoded)
    return decoded

#def rle_decode(data):
    decoded = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]
        if byte & 0x80:  # High bit set indicates a run
            run_length = (byte & 0x7F) + 1
            i += 1
            run_value = data[i]
            decoded.extend([run_value] * (run_length))
        else:
            literal_length = (byte & 0x7F) + 1
            i += 1
            decoded.extend(data[i:i+literal_length])
            i += literal_length - 1
        i += 1
    #decodeddata = struct.pack("B"*len(decoded), decoded)
    return decoded


def main():
    print("Hello from rct_progress!")
    fname = "CSS0.DAT"
    data = read_rct_progress(fname)

if __name__ == "__main__":
    main()

    