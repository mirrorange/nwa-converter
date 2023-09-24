from io import BytesIO

class BitReader:
    def __init__(self, data: BytesIO):
        self.data = data
        self.current = 0
        self.bit_pos = 8

    def read_bits(self, n):
        bits = 0
        pos = 0
        while n > 0:
            r = self.read_at_most(n)
            bits = bits | (r['bits'] << pos)
            pos += r['read']
            n -= r['read']
        return bits

    def read_at_most(self, n):
        bits = self.current
        bits = bits >> self.bit_pos
        bits = bits & ((1 << n) - 1)
        read = 8 - self.bit_pos
        if read > n:
            read = n
        self.bit_pos += read
        if self.bit_pos == 8:
            self.bit_pos = 0
            self.current = int.from_bytes(self.data.read(1), byteorder='big')
        return {'read': read, 'bits': bits}