# Class for working with Silky LZSS compression.
# So tiresome...

# Made by Tester Testerov.
# Partially based on original 4/6/1989 Haruhiko Okumura implementation.
# Has many differences, through, and not just cosmetic.
# Because Silky Engine's implementation is different itself. It is more closer to...
# Oh, probably, Saxman compression?


class SilkyLZSS:
    def __init__(self, buffer: bytes, N: int = 4096, F: int = 18, threshold: int = 2, null: int = None,
                 debug: bool = False, progress_print: int = 2 ** 15, padding_byte=b'\x00'):

        self.debug = debug
        self.input_buffer = buffer

        if null is None:  # No, thou cannot just take None there. Or program will [REDACTED]!!
            self.null = N
        else:
            self.null = null

        if isinstance(padding_byte, int):
            self.padding_byte = self.unsigned_char(padding_byte)
        else:
            self.padding_byte = padding_byte[0]
        self.progress_print = progress_print  # Duration of progress print.

        self.N = N  # Buffer size. In classical implementation it is 2^14. More buffer size is, the lesser file becomes.
        self.F = F  # Match length limit. In original implementation it is 18. More limit is, the lesser file becomes.
        self.threshold = threshold  # Minimum limit of match length to encode as position and length.
        # I strongly recommend thou use default threshold value.

        self.text_buffer = [0] * (self.N + self.F - 1)
        self.match_position = 0
        self.match_length = 0

        self.lson = [0] * (self.N + 1)
        self.rson = [0] * (self.N + 257)
        self.dad = [0] * (self.N + 1)

        self.length_crutch = 0

    def init_tree(self) -> None:
        for i in range(self.N + 1, self.N + 257):
            self.rson[i] = self.null
        for i in range(self.N):
            self.dad[i] = self.null

    def insert_node(self, r: int) -> None:
        """Insert string (len(s) = F) from buffer into one of the trees and returns the longest match."""
        i = 0
        cmp = 1

        p = self.N + 1 + self.text_buffer[r]
        self.rson[r] = self.null
        self.lson[r] = self.null
        self.match_length = 0
        while True:
            if cmp >= 0:
                if self.rson[p] != self.null:
                    p = self.rson[p]
                else:
                    self.rson[p] = r
                    self.dad[r] = p
                    return
            else:
                if self.lson[p] != self.null:
                    p = self.lson[p]
                else:
                    self.lson[p] = r
                    self.dad[r] = p
                    return
            for i in range(1, self.F):
                cmp = self.text_buffer[r + i] - self.text_buffer[p + i]
                if cmp != 0:
                    i -= 1
                    break
            i += 1
            if i > self.match_length:
                self.match_position = p
                self.match_length = i
                if self.match_length >= self.F:
                    break
        self.dad[r] = self.dad[p]
        self.lson[r] = self.lson[p]
        self.rson[r] = self.rson[p]
        self.dad[self.lson[p]] = r
        self.dad[self.rson[p]] = r
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = r
        else:
            self.lson[self.dad[p]] = r
        self.dad[p] = self.null

    def delete_node(self, p: int) -> None:
        """Delete node p."""
        if self.dad[p] == self.null:
            return
        if self.rson[p] == self.null:
            q = self.lson[p]
        elif self.lson[p] == self.null:
            q = self.rson[p]
        else:
            q = self.lson[p]
            if self.rson[q] != self.null:
                q = self.rson[q]
                while self.rson[q] != self.null:
                    q = self.rson[q]
                self.rson[self.dad[q]] = self.lson[q]
                self.dad[self.lson[q]] = self.dad[q]
                self.lson[q] = self.lson[p]
                self.dad[self.lson[p]] = q
            self.rson[q] = self.rson[p]
            self.dad[self.rson[p]] = q
        self.dad[q] = self.dad[p]
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = q
        else:
            self.lson[self.dad[p]] = q
        self.dad[p] = self.null

    def encode(self) -> bytes:
        i = -1
        length = -1
        r = self.N - self.F
        s = 0
        code_buf = [0] * 17
        mask = 1
        code_buf_ptr = mask
        output_buffer = b''

        self.init_tree()

        code_buf[0] = 0  # Delete?
        for i in range(s, r):
            self.text_buffer[i] = self.padding_byte
        for length in range(0, self.F):
            if length >= len(self.input_buffer):
                length -= 1
                break
            self.text_buffer[r + length] = self.input_buffer[length]
        length += 1  # Necessary crutch.
        if length == 0:
            return b''
        for i in range(1, self.F + 1):
            self.insert_node(r - i)
        self.insert_node(r)

        pos = i  # Crutch variable to fetch correct entries from input_buffer.

        print_count = 0

        while True:
            if self.match_length > length:  # Probably correct.
                self.match_length = length
            if self.match_length <= self.threshold:  # Correct.
                self.match_length = 1
                code_buf[0] |= mask
                code_buf[code_buf_ptr] = self.text_buffer[r]
                code_buf_ptr += 1
            else:  # Correct.
                code_buf[code_buf_ptr] = self.unsigned_char(self.match_position)
                code_buf_ptr += 1
                code_buf[code_buf_ptr] = self.unsigned_char((((self.match_position >> 4) & 0xf0) |
                                                             (self.match_length - (self.threshold + 1))))
                code_buf_ptr += 1
            mask <<= 1
            mask %= 256  # In that implementation was used just an unsigned char! #ERR!!!
            if mask == 0:  # Probably right.
                for i in range(0, code_buf_ptr):
                    output_buffer += code_buf[i].to_bytes(1, byteorder="big")  # Matches.
                i += 1
                code_buf[0] = 0
                code_buf_ptr = 1
                mask = 1
            last_match_length = self.match_length  # Matches.

            for i in range(0, last_match_length):
                if pos >= len(self.input_buffer):
                    i -= 1
                    break
                self.delete_node(s)
                c = self.input_buffer[pos]
                pos += 1
                self.text_buffer[s] = c
                if s < (self.F - 1):
                    self.text_buffer[s + self.N] = c
                s = (s + 1) & (self.N - 1)
                r = (r + 1) & (self.N - 1)
                self.insert_node(r)
            i += 1  # Alas, this crutch is necessary.

            if pos > print_count:  # Frankly, not very important, but...
                if self.debug:
                    print("{}\r".format(pos))
                print_count += self.progress_print

            while i < last_match_length:
                i += 1
                self.delete_node(s)
                s = (s + 1) & (self.N - 1)
                r = (r + 1) & (self.N - 1)
                length -= 1
                if length:
                    self.insert_node(r)
            i += 1
            if length <= 0:
                break

        if code_buf_ptr > 1:
            for i in range(0, code_buf_ptr):
                output_buffer += code_buf[i].to_bytes(1, byteorder="big")
        if self.debug:
            print("In: {} bytes.".format(len(self.input_buffer)))
            print("Out: {} bytes.".format(len(output_buffer)))
            print("Out/In: {}.".format(round(len(self.input_buffer) / len(output_buffer), 4)))

        return output_buffer

    def decode(self) -> bytes:
        """Decode bytes from lzss."""

        output_buffer = b''
        r = self.N - self.F
        flags = 0

        text_buffer = [0] * r

        self.init_tree()

        for i in range(0, r):
            self.text_buffer[i] = self.padding_byte

        current_pos = 0

        while True:
            flags >>= 1
            if (flags & 256) == 0:
                if current_pos >= len(self.input_buffer):
                    break
                c = self.input_buffer[current_pos]
                current_pos += 1
                flags = c | 0xff00
            if flags & 1:
                if current_pos >= len(self.input_buffer):
                    break
                c = self.input_buffer[current_pos]
                current_pos += 1
                output_buffer += c.to_bytes(1, byteorder="big")
                self.text_buffer[r] = c
                r += 1
                r &= self.N - 1
            else:
                if current_pos >= len(self.input_buffer):
                    break
                i = self.input_buffer[current_pos]
                current_pos += 1
                if current_pos >= len(self.input_buffer):
                    break
                j = self.input_buffer[current_pos]
                current_pos += 1
                i |= (j & 0xf0) << 4
                j = (j & 0x0f) + self.threshold
                for k in range(0, j + 1):
                    c = self.text_buffer[(i + k) & (self.N - 1)]
                    output_buffer += c.to_bytes(1, byteorder="big")
                    self.text_buffer[r] = c
                    r += 1
                    r &= self.N - 1
        return output_buffer

    @staticmethod
    def unsigned_char(char: int):
        """Convert into unsigned char."""
        return char % 256
