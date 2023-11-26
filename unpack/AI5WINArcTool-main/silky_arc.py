import struct
import os
import tempfile
from silky_lzss import SilkyLZSS

# 4 байта I: длина описания файлов.
# Далее идёт следующий сегмент (с повторениями):
##1 байт длина имени файла.
###Далее столько идёт длина имени файла.
###Далее 4 байта >I размер после lzss-компрессии.
###Далее 4 байта >I размер до lzss-компрессии.
###Далее 4 байта >I смещение относительно начала файла.
# Далее идёт сегмент, где сплошняком записываются сами файлы по параметрам в описании.


class SilkyArc:
    name_encoding = "cp932"

    def __init__(self, arc: str, dir: str, verbose: bool = True, integrity_check: bool = False):
        """Parameters:
arc: name of the archive file,
dir: name of the directory,
verbose: False (no progress messages) or True (enable progress messages)."""
        self._arc_name = arc
        self._dir_name = dir

        self._verbose = verbose
        self._integrity_check = integrity_check

        self._names = []
        # 0 -- name length, 1 -- name, 2 -- compressed in lzss size, 3 -- size after lzss decompression,
        # 4 -- offset from the beginning of file.

    # Основные пользовательские методы.

    def unpack(self) -> None:
        if self._verbose:
            print("=== === === UNPACKING OF {0} STARTS!/РАСПАКОВКА {0} НАЧАТА! === === ===".format(self._arc_name))
        self._names = self._unpack_names()
        if self._verbose:
            print("=== Header of {0} unpacked!/Заголовок {0} распакован! ===".format(self._arc_name))
        self._unpack_files()
        if self._verbose:
            print("=== Files of {0} unpacked!/Файлы {0} распакованы! ===".format(self._arc_name))
            print("=== === === UNPACKING OF {0} ENDS!/РАСПАКОВКА {0} ЗАКОНЧЕНА! === === ===".format(self._arc_name))

    def pack(self) -> None:
        if self._verbose:
            print("=== === === PACKING OF {0} STARTS!/ЗАПАКОВКА {0} НАЧАТА! === === ===".format(self._arc_name))
        head_len, self._names, temp_file = self._pack_names_and_files()
        if self._verbose:
            print("=== Data of {0} initialized!/Данные {0} определены! ===".format(self._arc_name))
        try:
            os.rename(self._arc_name, self._arc_name + '.bak')
        except OSError:
            pass
        self._pack_files(head_len, temp_file)
        if self._verbose:
            print("=== Archive {0} successfully compiled!/Архив {0} успешно собран! ===".format(self._arc_name))
            print("=== === === PACKING OF {0} ENDS!/ЗАПАКОВКА {0} ЗАКОНЧЕНА! === === ===".format(self._arc_name))

    # Special techmocal methods: Silky Engine's implementation of lzss.

    @staticmethod
    def lzss_compress(byter: bytes) -> bytes:
        """Compress bytes with lzss."""

        dec = SilkyLZSS(byter)
        new_bytes = dec.encode()

        return new_bytes

    @staticmethod
    def lzss_decompress(byter: bytes) -> bytes:
        """Decompress bytes with lzss."""

        dec = SilkyLZSS(byter)
        new_bytes = dec.decode()

        return new_bytes

    # Unpacking methods.

    def _read_header(self, filer) -> int:
        return struct.unpack('I', filer.read(4))[0]

    def _unpack_names(self) -> list:
        input_file = open(self._arc_name, 'rb')
        limit = self._read_header(input_file)
        array_name = []
        while (input_file.tell() < limit):
            name_len = input_file.read(1)[0]
            name = self.decrypt_name(input_file.read(name_len))
            prms = []
            # 0 - размер.
            # 1 - размер после декомпрессии lzss.
            # 2 - начальное смещение.
            for i in range(3):
                prms.append(struct.unpack('>I', input_file.read(4))[0])
            array_name.append([name_len, name, prms[0], prms[1], prms[2]])
        input_file.close()
        return array_name

    def _unpack_files(self) -> None:
        os.makedirs(self._dir_name, exist_ok=True)
        input_file = open(self._arc_name, 'rb')

        for i in self._names:
            this_file_name = os.path.normpath(os.path.join(self._dir_name, i[1]))
            input_file.seek(i[4], 0)
            new_file_bytes = input_file.read(i[2])
            if self._integrity_check:
                try:
                    assert len(new_file_bytes) == i[2]
                except AssertionError:
                    print("!!! File {0} compressed size is incorrect!/Размер сжатого файла {0} некорректен!".
                          format(i[1]))
            if i[2] != i[3]:  # If the entry is encrypted...
                new_file_bytes = self.lzss_decompress(new_file_bytes)
                if self._integrity_check:
                    try:
                        assert len(new_file_bytes) == i[3]
                    except AssertionError:
                        print("!!! File {0} true size is incorrect!/Истинный размер файла {0} некорректен!".
                              format(i[1]))
            with open(this_file_name, 'wb') as this_file:
                this_file.write(new_file_bytes)
            if self._verbose:
                print("> File {0} successfully unpacked!/Файл {0} успешно распакован!".format(i[1]))

        input_file.close()

    # Packing methods.

    def _pack_names_and_files(self) -> tuple:
        names = []
        sum = 0

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

                name_array.append(len(encrypted_name))  # Length of encrypted name.
                name_array.append(encrypted_name)  # Filename (encrypted).
                name_array.append(len(encrypted_bytes))  # Filename (encrypted).
                name_array.append(len(this_bytes))  # Filename (encrypted).
                name_array.append(None)  # Offset from the start of file (currently unknown).

                names.append(name_array)

                sum += len(encrypted_name) + 13
                # 1 байт за размер имени, далее имя, далее три >I параметра.

                if self._verbose:
                    print("> File {0} successfully managed!/Файл {0} успешно обработан!".format(end_name))

        head_len = sum
        sum += 4
        # Теперь sum на смещении первого файла.

        for i in range(len(names)):
            names[i][4] = sum
            sum += names[i][2]
        if self._verbose:
            print(">>> File offsets successfully calculated!/Смещения файлов успешно подсчитаны!")

        return head_len, names, temp_file

    def _pack_files(self, head_len: int, temp_file: tempfile.TemporaryFile) -> None:
        new_archive = open(self._arc_name, 'wb')
        new_archive.write(struct.pack('I', head_len))

        for i in self._names:
            new_archive.write(struct.pack('B', i[0]))
            new_archive.write(i[1])
            for j in range(2, 5):
                new_archive.write(struct.pack('>I', i[j]))
        if self._verbose:
            print(">>> Archive header successfully created!/Заголовок архива успешно создан!")

        temp_file.seek(0)
        for i in self._names:
            new_bytes = temp_file.read(i[2])
            if self._integrity_check:
                try:
                    assert len(new_bytes) == i[2]
                except AssertionError:
                    print("!!! File {0} compressed size is incorrect!/Размер сжатого файла {0} некорректен!".format(
                        self.decrypt_name(i[1])))
            new_archive.write(new_bytes)
        if self._verbose:
            print(">>> Archive files data successfully packed!/Данные файлов архива успешно запакованы!")

        new_archive.close()
        temp_file.close()

    # Other technical methosd.

    @staticmethod
    def decrypt_name(test: bytes) -> str:
        tester = b''
        k = 0
        for i in range(len(test) - 1, -1, -1):
            k += 1
            tester = struct.pack('B', test[i] + k) + tester
        name = tester.decode(SilkyArc.name_encoding)
        return name

    @staticmethod
    def encrypt_name(test: str) -> bytes:
        text_array = test.encode(SilkyArc.name_encoding)
        tester = b''
        k = 0
        for i in range(len(text_array) - 1, -1, -1):
            k += 1
            tester = struct.pack('B', text_array[i] - k) + tester
        return tester
