from io import BufferedReader, BytesIO
from bitreader import BitReader
import shutil
import struct

class NWAHeader:
    channels: int
    bps: int
    freq: int
    complevel: int
    userunlength: int
    blocks: int
    datasize: int
    compdatasize: int
    samplecount: int
    blocksize: int
    restsize: int
    offsets: list

    def __init__(self, file: BufferedReader = None):
        self.channels = struct.unpack("<h", file.read(2))[0]
        self.bps = struct.unpack("<h", file.read(2))[0]
        self.freq = struct.unpack("<i", file.read(4))[0]
        self.complevel = struct.unpack("<i", file.read(4))[0]
        self.userunlength = struct.unpack("<i", file.read(4))[0]
        self.blocks = struct.unpack("<i", file.read(4))[0]
        self.datasize = struct.unpack("<i", file.read(4))[0]
        self.compdatasize = struct.unpack("<i", file.read(4))[0]
        self.samplecount = struct.unpack("<i", file.read(4))[0]
        self.blocksize = struct.unpack("<i", file.read(4))[0]
        self.restsize = struct.unpack("<i", file.read(4))[0]
        _dummy = struct.unpack("<i", file.read(4))[0]

        if self.complevel == -1:
            self.blocksize = 65536
            self.restsize = (self.datasize % (self.blocksize * (self.bps // 8))) // (
                self.bps // 8
            )
            rest = 0
            if self.restsize > 0:
                rest = 1
            self.blocks = (self.datasize // (self.blocksize * (self.bps // 8))) + rest
        if self.blocks <= 0 or self.blocks > 1000000:
            raise ValueError(f"blocks are too large: {self.blocks}")

        self.offsets = [0] * self.blocks
        if self.complevel != -1:
            # Read the offset indexes
            for i in range(self.blocks):
                self.offsets[i] = struct.unpack("<i", file.read(4))[0]
        return

    def check(self):
        # Check if the header is valid
        if self.complevel != -1 and not self.offsets:
            raise ValueError("no offsets set even thought they are needed")
        if self.channels != 1 and self.channels != 2:
            raise ValueError(
                f"this library only supports mono / stereo data: data has {self.channels} channels"
            )
        if self.bps != 8 and self.bps != 16:
            raise ValueError(
                f"this library only supports 8 / 16bit data: data is {self.bps} bits"
            )
        if self.complevel == -1:
            byps = self.bps // 8  # Bytes per sample
            if self.datasize != self.samplecount * byps:
                raise ValueError(
                    f"invalid datasize: datasize {self.datasize} != samplecount {self.samplecount} * samplesize {byps}"
                )
            if self.samplecount != (self.blocks - 1) * self.blocksize + self.restsize:
                raise ValueError(
                    f"total sample count is invalid: samplecount {self.samplecount} != {self.blocks-1}*{self.blocksize}+{self.restsize}(block*blocksize+lastblocksize)"
                )
            return
        if self.complevel < -1 or self.complevel > 5:
            raise ValueError(
                f"this library supports only compression level from -1 to 5: the compression level of the data is {self.complevel}"
            )
        if self.offsets[self.blocks - 1] >= self.compdatasize:
            raise ValueError("the last offset overruns the file.")
        byps = self.bps // 8  # Bytes per sample
        if self.datasize != self.samplecount * byps:
            raise ValueError(
                f"invalid datasize: datasize {self.datasize} != samplecount {self.samplecount} * samplesize {byps}"
            )
        if self.samplecount != (self.blocks - 1) * self.blocksize + self.restsize:
            raise ValueError(
                f"total sample count is invalid: samplecount {self.samplecount} != {self.blocks-1}*{self.blocksize}+{self.restsize}(block*blocksize+lastblocksize)."
            )


class NWAFile:
    header: NWAHeader
    data: BytesIO
    cur_block: int

    def __init__(self, file: BufferedReader):
        self.header = NWAHeader(file)
        self.header.check()

        # Calculate target data size
        # WAVE header = 36 bytes
        size = 36 + self.header.datasize
        self.data = BytesIO(bytes([0] * size))
        self.cur_block = 0

        # Write the WAVE header
        self.write_wave_header()

        done = 0
        while done < self.header.datasize:
            done += self.decode_block(file)
            print(f"Decoding: {done} / {self.header.datasize}\r", end="")

    def write_wave_header(self):
        byps = (self.header.bps + 7) >> 3

        self.data.write(b"RIFF")
        self.data.write(struct.pack("<i", (self.header.datasize + 0x24)))
        self.data.write(b"WAVEfmt ")
        self.data.write(b"\x10\x00\x00\x00\x01\x00")
        self.data.write(struct.pack("<h", self.header.channels))
        self.data.write(struct.pack("<i", self.header.freq))
        self.data.write(
            struct.pack("<i", byps * self.header.freq * self.header.channels)
        )
        self.data.write(struct.pack("<h", byps * self.header.channels))
        self.data.write(struct.pack("<h", self.header.bps))
        self.data.write(b"data")
        self.data.write(struct.pack("<i", self.header.datasize))

    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(self.data.getvalue())

    def decode_block(self, file: BufferedReader):
        # Uncompressed wave data stream
        if self.header.complevel == -1:
            self.cur_block = self.header.blocks
            start_len = len(self.data.getvalue())
            shutil.copyfileobj(file, self.data)
            end_len = len(self.data.getvalue())
            ret = end_len - start_len
            return ret

        if self.header.blocks == self.cur_block:
            return 0

        # Calculate the size of the decoded block
        if self.cur_block != self.header.blocks - 1:
            cur_blocksize = self.header.blocksize * (self.header.bps // 8)
            curcompsize = (
                self.header.offsets[self.cur_block + 1]
                - self.header.offsets[self.cur_block]
            )
            if cur_blocksize >= self.header.blocksize * (self.header.bps // 8) * 2:
                raise ValueError("Current block exceeds the excepted count.")
        else:
            cur_blocksize = self.header.restsize * (self.header.bps // 8)
            curcompsize = self.header.blocksize * (self.header.bps // 8) * 2

        # Read in the block data
        buf = BytesIO(file.read(curcompsize))

        # Decode the compressed block
        self.decode(buf, cur_blocksize)

        self.cur_block += 1
        return cur_blocksize

    def decode(self, buf: BytesIO, outsize: int):
        d = [0, 0]
        flipflag = 0
        runlength = 0

        # Read the first data (with full accuracy)
        if self.header.bps == 8:
            d[0] = struct.unpack("<B", buf.read(1))[0]
        else:
            # bps == 16bit
            d[0] = struct.unpack("<H", buf.read(2))[0]

        # Stereo
        if self.header.channels == 2:
            if self.header.bps == 8:
                d[1] = struct.unpack("<B", buf.read(1))[0]
            else:
                # bps == 16bit
                d[1] = struct.unpack("<H", buf.read(2))[0]

        reader = BitReader(buf)

        dsize = outsize // (self.header.bps // 8)
        t = 0
        for _ in range(dsize):
            t += 1
            # If we are not in a copy loop (RLE), read in the data
            if runlength == 0:
                exponent = reader.read_bits(3)
                # Branching according to the mantissa: 0, 1-6, 7
                if exponent == 7:
                    # 7: big exponent
                    # In case we are using RLE (complevel==5) this is disabled
                    if reader.read_bits(1) == 1:
                        d[flipflag] = 0
                    else:
                        bits = (
                            8
                            if self.header.complevel >= 3
                            else 8 - self.header.complevel
                        )
                        shift = (
                            9
                            if self.header.complevel >= 3
                            else 2 + 7 + self.header.complevel
                        )
                        mask1 = 1 << (bits - 1)
                        mask2 = (1 << (bits - 1)) - 1
                        b = reader.read_bits(bits)
                        if b & mask1 != 0:
                            d[flipflag] -= (b & mask2) << shift
                        else:
                            d[flipflag] += (b & mask2) << shift
                elif 1 <= exponent <= 6:
                    # 1-6 : normal differencial
                    bits = (
                        self.header.complevel + 3
                        if self.header.complevel >= 3
                        else 5 - self.header.complevel
                    )
                    shift = (
                        1 + exponent
                        if self.header.complevel >= 3
                        else 2 + exponent + self.header.complevel
                    )
                    mask1 = 1 << (bits - 1)
                    mask2 = (1 << (bits - 1)) - 1
                    b = reader.read_bits(bits)
                    if b & mask1 != 0:
                        d[flipflag] -= (b & mask2) << shift
                    else:
                        d[flipflag] += (b & mask2) << shift
                elif exponent == 0:
                    # Skips when not using RLE
                    if self.header.userunlength == 1:
                        runlength = reader.read_bits(1)
                        if runlength == 1:
                            runlength = reader.read_bits(2)
                            if runlength == 3:
                                runlength = reader.read_bits(8)
            else:
                runlength -= 1
            if self.header.bps == 8:
                self.data.write(struct.pack("<B", d[flipflag]))
            else:
                self.data.write(struct.pack("<h", (d[flipflag] + 2**15) % 2**16 - 2**15))
            if self.header.channels == 2:
                # Changing the channel
                flipflag ^= 1