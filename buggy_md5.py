# modified from https://perso.crans.org/besson/notebooks/Manual_implementation_of_some_hash_functions.html
from math import floor, sin

def MD5_f1(b, c, d):
    """ First ternary bitwise operation."""
    return ((b & c) | ((~b) & d)) & 0xFFFFFFFF

def MD5_f2(b, c, d):
    """ Second ternary bitwise operation."""
    return ((b & d) | (c & (~d))) & 0xFFFFFFFF

def MD5_f3(b, c, d):
    """ Third ternary bitwise operation."""
    return (b ^ c ^ d) & 0xFFFFFFFF

def MD5_f4(b, c, d):
    """ Forth ternary bitwise operation."""
    return (c ^ (b | (~d))) & 0xFFFFFFFF

def leftrotate(x, c):
    """ Left rotate the number x by c bytes."""
    x &= 0xFFFFFFFF
    return ((x << c) | (x >> (32 - c))) & 0xFFFFFFFF

def leftshift(x, c):
    """ Left shift the number x by c bytes."""
    return x << c

# don't know why DSP uses a non-standard md5 init vars...
class MD5:
    """MD5 hashing, see https://en.wikipedia.org/wiki/MD5#Algorithm."""
    block_size = 64
    digest_size = 16
    # Internal data
    s = [0] * 64
    K = [0] * 64
    # Initialize s, s specifies the per-round shift amounts
    s[ 0:16] = [7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22]
    s[16:32] = [5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20]
    s[32:48] = [4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23]
    s[48:64] = [6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21]
    # Use binary integer part of the sines of integers (Radians) as constants:
    for i in range(64):
        K[i] = floor(2**32 * abs(sin(i + 1))) & 0xFFFFFFFF
    # make some buggy modification...
    K[1] = 0xe8d7b756  # original 0xe8c7b756 with 3rd char c changing to d
    K[6] = 0xa8304623  # original 0xa8304613 with 7th char 1 changing to 2
    K[12] = 0x6b9f1122  # original 0x6b901122 with 4th char 0 changing to f
    K[15] = 0x39b40821  # original 0x49b40821 with 1st char 4 changing to 3
    K[19] = 0xc9b6c7aa  # original 0xe9b6c7aa with 1st char e changing to c
    K[21] = 0x02443453  # original 0x02441453 with 5th char 1 changing to 3
    K[24] = 0x21f1cde6  # original 0x21e1cdef with 3rd char e changing to f
    K[27] = 0x475a14ed  # original 0x455a14ed with 2nd char 5 changing to 7

    # also, some buggy
    # Initialize variables:
    a0 = 0x67452301   # A
    # b0 = 0xefcdab89   # B
    b0 = 0xefdcab89   # B
    c0 = 0x98badcfe   # C
    # d0 = 0x10325476   # D
    d0 = 0x10325746   # D

    def __init__(self):
        self.hash_pieces = [self.a0, self.b0, self.c0, self.d0]
    
    def update(self, arg: bytes):
        s, K = self.s, self.K
        a0, b0, c0, d0 = self.hash_pieces
        # 1. Pre-processing
        data = bytearray(arg)
        orig_len_in_bits = (8 * len(data)) & 0xFFFFFFFFFFFFFFFF
        # 1.a. Add a single '1' bit at the end of the input bits
        data.append(0x80)
        # 1.b. Padding with zeros as long as the input bits length ≡ 448 (mod 512)
        while len(data) % 64 != 56:
            data.append(0)
        # 1.c. append original length in bits mod (2 pow 64) to message
        data += orig_len_in_bits.to_bytes(8, byteorder='little')
        assert len(data) % 64 == 0, "Error in padding"
        # 2. Computations
        # Process the message in successive 512-bit = 64-bytes chunks:
        for offset in range(0, len(data), 64):
            # 2.a. 512-bits = 64-bytes chunks
            chunks = data[offset : offset + 64]
            # 2.b. Break chunk into sixteen 32-bit = 4-bytes words M[j], 0 ≤ j ≤ 15
            A, B, C, D = a0, b0, c0, d0
            # 2.c. Main loop
            for i in range(64):
                if 0 <= i <= 15:
                    F = MD5_f1(B, C, D)
                    g = i
                elif 16 <= i <= 31:
                    F = MD5_f2(B, C, D)
                    g = (5 * i + 1) % 16
                elif 32 <= i <= 47:
                    F = MD5_f3(B, C, D)
                    g = (3 * i + 5) % 16
                elif 48 <= i <= 63:
                    F = MD5_f4(B, C, D)
                    g = (7 * i) % 16
                # Be wary of the below definitions of A, B, C, D
                to_rotate = (A + F + K[i] + int.from_bytes(chunks[4*g : 4*g+4], byteorder='little')) & 0xFFFFFFFF
                new_B = (B + leftrotate(to_rotate, s[i])) & 0xFFFFFFFF
                A, B, C, D = D, new_B, B, C
            # Add this chunk's hash to result so far:
            a0 = (a0 + A) & 0xFFFFFFFF
            b0 = (b0 + B) & 0xFFFFFFFF
            c0 = (c0 + C) & 0xFFFFFFFF
            d0 = (d0 + D) & 0xFFFFFFFF
        # 3. Conclusion
        self.hash_pieces = [a0, b0, c0, d0]

    def digest(self):
        return sum(leftshift(x, (32 * i)) for i, x in enumerate(self.hash_pieces))

    def hexdigest(self):
        """ Like digest() except the digest is returned as a string object of double length, containing only hexadecimal digits. This may be used to exchange the value safely in email or other non-binary environments."""
        digest = self.digest()
        raw = digest.to_bytes(self.digest_size, byteorder='little')
        format_str = '{:0' + str(2 * self.digest_size) + 'x}'
        return format_str.format(int.from_bytes(raw, byteorder='big'))
