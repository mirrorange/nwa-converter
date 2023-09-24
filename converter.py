import os
import time
import struct
from typing import List
from nwafile import NWAFile


class IndexEntry:
    def __init__(self, size: int, offset: int, count: int):
        self.size = size
        self.offset = offset
        self.count = count


class NWAConverter:
    file_path: str
    save_dir: str
    file_name: str
    file_stem: str
    ext: str

    def __init__(self, file_path, save_dir) -> None:
        self.file_path = file_path
        self.save_dir = save_dir
        self.file_name = os.path.basename(file_path)
        self.file_stem, self.ext = os.path.splitext(self.file_name)

    def convert(self):
        start_time = time.time()
        file_path = self.file_path
        ext = self.ext
        print(f"converting file: {self.file_name}")

        if ext == ".nwa":
            with open(file_path, "rb") as file:
                nwa_file = NWAFile(file)
                nwa_file.save(os.path.join(self.save_dir, f"{self.file_stem}.wav"))
        elif ext == ".nwk":
            index = self.read_index(12)
            for i in index:
                self.save_wav(i)
        elif ext == ".ovk":
            index = self.read_index(16)
            for i in index:
                self.save_ogg(i)
        else:
            raise ValueError(f"unsupported file: {ext}")
        
        print(f"finished converting file: {self.file_name} in {time.time() - start_time} seconds")

    def save_wav(self, i: IndexEntry):
        with open(self.file_path, "rb") as file:
            file.seek(i.offset)
            nwa = NWAFile(file)
            nwa.save(os.path.join(self.save_dir, f"{self.file_stem}-{i.count}.wav"))

    def save_ogg(self, i: IndexEntry):
        file_path = self.file_path
        file_stem = self.file_stem
        with open(file_path, "rb") as file:
            file.seek(i.offset)
            buf = file.read(i.size)

            with open(f"{file_stem}-{i.count}.ogg", "wb") as out_file:
                out_file.write(buf)

    def read_index(self, head_block_size: int) -> List[IndexEntry]:
        with open(self.file_path, "rb") as file:
            indexcount = struct.unpack("<i", file.read(4))[0]
            if indexcount <= 0:
                raise ValueError(f"invalid indexcount found: {indexcount}")

            index = []
            for _ in range(indexcount):
                buf = file.read(head_block_size)
                size, offset, count = struct.unpack("<iii", buf)

                if offset <= 0 or size <= 0:
                    raise ValueError(
                        f"invalid table entry. offset: {offset}, size: {size}"
                    )

                index.append(IndexEntry(size, offset, count))

            return index