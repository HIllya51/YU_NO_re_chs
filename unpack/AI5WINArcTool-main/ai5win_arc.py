# Class for packing and unpacking AI6WIN .arc archives.
# Before I hath implemented Silky Engine's arc. Now it is time for this one...
# These archives are quite far, yet they has some common traits.
# Namely, names obfusification and compression.

# Header.
## 4 bytes for number of entries.
## In each entry:
### N bytes (20, 30, 32, 256...) for name (encrypted/obfusificated, see "decrypt_name".
### 4 bytes (<I) for LZSS compressed size.
### 4 bytes (<I) for uncompressed size.
### 4 bytes (<I) for data offset from the beginning of file.
## Next is data... Compressed by Silky's implementation of LZSS.

import os
import struct
import tempfile
from silky_arc import SilkyArc


class AI5WINArc(SilkyArc):  # Previously released tool came to be handy.
    # Some part of the class is from SilkyArcTool.
    name_encoding = "cp932"
    possible_name_bytes = (12, 20, 30, 32, 256)
    header_int_structure = "I"  # Just to be safe make this a parameter.

    known_keys_triplets = (
        (95, 1182992201, 391284862),
        (3, 0x33656755, 0x68820811),
        (0x55, 0xaa55aa55, 0x55aa55aa),  # Doukyuusei 2.
    )

    def __init__(self, arc: str, dir: str, verbose: bool = True, integrity_check: bool = False, **kwargs):
        """Parameters:
arc: name of the archive file,
dir: name of the directory,
verbose: False (no progress messages) or True (enable progress messages).
first_key: int, key for text in header.
second_key: int, key for size in header.
third_key: int, key for offset in header.
name_bytes: int, number of bytes for a name.
"""
        super().__init__(arc, dir, verbose, integrity_check)

        self.first_key = kwargs.get("first_key", None)
        self.second_key = kwargs.get("second_key", None)
        self.third_key = kwargs.get("third_key", None)
        self.name_bytes = kwargs.get("name_bytes", None)

        # names
        # 0 -- name, 1 -- compressed in lzss size, 2 -- offset from the beginning of the file.

    # imported methods: unpack, pack, lzss_compress, lzss_decompress, read_header...

    # Unpacking methods.

    def _unpack_names(self) -> list:
        """Unpack archive names."""
        input_file = open(self._arc_name, 'rb')
        self.first_key, self.second_key, self.third_key, self.name_bytes = self.hack_size_and_crypto_keys(input_file)
        entry_count = self._read_header(input_file)

        array_name = []
        keyer = (self.second_key, self.third_key)
        for entrer in range(entry_count):
            prms = []
            name = self.decrypt_name(input_file.read(self.name_bytes))
            if '\x00' in name:  # Some crutch to fix "garbage archives".
                name = name.split('\x00')[0]
            prms.append(name)
            for key in keyer:
                prms.append(struct.unpack(self.header_int_structure, input_file.read(4))[0] ^ key)
            array_name.append(prms)

        input_file.close()  # Header len is 4 + entry_count*(32+4*2)

        return array_name

    def _unpack_files(self) -> None:
        """Unpack archive files."""
        os.makedirs(self._dir_name, exist_ok=True)
        input_file = open(self._arc_name, 'rb')

        for i in self._names:
            this_file_name = os.path.normpath(os.path.join(self._dir_name, i[0]))
            input_file.seek(i[2], 0)
            new_file_bytes = input_file.read(i[1])
            if self._integrity_check:
                try:
                    assert len(new_file_bytes) == i[1]
                except AssertionError:
                    print("!!! File {0} compressed size is incorrect!/Размер сжатого файла {0} некорректен!".
                          format(i[1]))
            new_file_bytes = self.lzss_decompress(new_file_bytes)
            with open(this_file_name, 'wb') as this_file:
                this_file.write(new_file_bytes)
            if self._verbose:
                print("> File {0} successfully unpacked!/Файл {0} успешно распакован!".format(i[0]))

        input_file.close()

    # Packing methods.

    def _pack_names_and_files(self) -> tuple:
        """Get data about archive names and prepack files into a temporary file."""
        names = []
        sum = 4

        temp_file = tempfile.TemporaryFile(mode="w+b")

        for root, dirs, files in os.walk(self._dir_name):
            for filename in files:
                name_array = []

                rel_name = os.path.normpath(os.path.join(root, filename))
                end_name = rel_name
                if rel_name.startswith(root + os.sep):
                    end_name = rel_name[len(root + os.sep):]
                encrypted_name = self.encrypt_name(end_name)

                with open(rel_name, 'rb') as this_file:
                    this_bytes = this_file.read()
                encrypted_bytes = self.lzss_compress(this_bytes)

                temp_file.write(encrypted_bytes)

                name_array.append(encrypted_name)  # Filename (encrypted).
                name_array.append(len(encrypted_bytes))  # Length of encrypted entry.
                # Ohhh... No integrity check data. Verily, 'tis sad.
                name_array.append(None)  # Offset from the start of file (currently unknown).

                names.append(name_array)

                sum += self.name_bytes + 8
                # 1 байт за размер имени, далее имя, далее три >I параметра.

                if self._verbose:
                    print("> File {0} successfully managed!/Файл {0} успешно обработан!".format(end_name))

        head_len = len(names)  # Not the header length, rather number of entries.

        for i in range(len(names)):
            names[i][2] = sum
            sum += names[i][1]
        if self._verbose:
            print(">>> File offsets successfully calculated!/Смещения файлов успешно подсчитаны!")

        return head_len, names, temp_file

    def _pack_files(self, head_len: int, temp_file: tempfile.TemporaryFile) -> None:
        """Pack data and files into the archive."""
        new_archive = open(self._arc_name, 'wb')
        new_archive.write(struct.pack('I', head_len))

        keyer = (self.second_key, self.third_key)
        for i in self._names:
            new_archive.write(i[0])
            for key, index in zip(keyer, range(1, 3)):
                new_archive.write(struct.pack(self.header_int_structure, i[index] ^ key))
        if self._verbose:
            print(">>> Archive header successfully created!/Заголовок архива успешно создан!")

        temp_file.seek(0)
        for i in self._names:
            new_bytes = temp_file.read(i[1])
            if self._integrity_check:
                try:
                    assert len(new_bytes) == i[1]
                except AssertionError:
                    print("!!! File {0} compressed size is incorrect!/Размер сжатого файла {0} некорректен!".format(
                        self.decrypt_name(i[0])))
            new_archive.write(new_bytes)
        if self._verbose:
            print(">>> Archive files data successfully packed!/Данные файлов архива успешно запакованы!")

        new_archive.close()
        temp_file.close()

    # Other technical methods.

    @staticmethod
    def hack_size_and_crypto_keys(input_file) -> tuple:
        """Hack all three keys used to encrypt/obfusificate the header and length of names.
Works only if the archive has at least 2 entries.
First key is for text, second key is for size, third is for offset."""

        current_offset = input_file.tell()

        bytes_for_name = 0
        first_key = 0
        second_key = 0
        third_key = 0

        for bytes_for_name in AI5WINArc.possible_name_bytes:
            input_file.seek(0, 0)
            entry_count = struct.unpack('I', input_file.read(4))[0]
            start_offset = 4 + entry_count * (bytes_for_name + 8)

            input_file.seek(4 + bytes_for_name - 1, 0)
            first_key = input_file.read(1)[0]
            bad_size = struct.unpack(AI5WINArc.header_int_structure, input_file.read(4))[0]
            third_key = struct.unpack(AI5WINArc.header_int_structure, input_file.read(4))[0] ^ start_offset

            input_file.seek(4 + (bytes_for_name + 8) + (bytes_for_name + 4), 0)
            next_offset = struct.unpack(AI5WINArc.header_int_structure, input_file.read(4))[0] ^ third_key
            good_size = next_offset - start_offset
            second_key = bad_size ^ good_size

            try:
                for entry in range(entry_count):
                    starter = 4 + entry*(8 + bytes_for_name)
                    input_file.seek(starter, 0)
                    new_bytes = input_file.read(bytes_for_name)
                    tester = b''
                    for i in new_bytes:
                        tester += struct.pack('B', i ^ first_key)
                    tester = tester.rstrip(b'\x00')
                    tester.decode(SilkyArc.name_encoding)
            except UnicodeDecodeError as ex:
                continue

            if good_size <= 0:
                continue

            break

        input_file.seek(current_offset, 0)

        print(">>< Hacked keys/Взломанные ключи:", hex(first_key), hex(second_key), hex(third_key))
        print(">>< Hacked name size/Взломанный размер имён:", bytes_for_name)

        return first_key, second_key, third_key, bytes_for_name

    def decrypt_name(self, test: bytes) -> str:
        """Decrypt AI5WIN-encrypted header entry name."""
        tester = b''
        for i in test:
            tester += struct.pack('B', i ^ self.first_key)
        tester = tester.rstrip(b'\x00')
        name = tester.decode(SilkyArc.name_encoding)
        return name

    def encrypt_name(self, test: str) -> bytes:
        """Encrypt AI5WIN-encrypted header entry name."""
        test = test.encode(AI5WINArc.name_encoding)
        check_len = len(test)
        if check_len >= (self.name_bytes - 1):
            test = test[:self.name_bytes - 1] + b'\x00'
        else:
            test += b'\x00' * (self.name_bytes - check_len)
        tester = b''
        for i in test:
            tester += struct.pack('B', i ^ self.first_key)
        return tester
