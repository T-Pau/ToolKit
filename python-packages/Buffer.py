class Buffer:
    def __init__(self, padding = 0, byteorder="little"):
        self.data = b""
        self.padding = padding
        self.byteorder = byteorder
    
    def add_byte(self, byte, count=1):
        self.data += byte.to_bytes(1, byteorder="little") * count
    
    def add_data(self, data, length=0, padding=None):
        if padding is None:
            padding = self.padding
        if type(data) is str:
            data = bytearray(data.upper(), "utf-8")
        self.data += data
        if len(data) < length:
            self.data += padding.to_bytes(1, byteorder="little") * (length - len(data))
    
    def add_word(self, word, byteorder=None):
        self.add_int(word, 2, byteorder)

    def add_long(self, value, byteorder=None):
        self.add_int(value, 4, byteorder)

    def add_int(self, value, size, byteorder=None):
        if byteorder is None:
            byteorder = self.byteorder
        self.data += value.to_bytes(size, byteorder=byteorder)

    def add_zeros(self, length):
        self.data += b"\x00" * length

    def clear(self):
        self.data = b""

    def pad(self, length, padding = None):
        if padding is None:
            padding = self.padding
        if len(self.data) < length:
            self.data += padding.to_bytes(1, byteorder="little") * (length - len(self.data))

    def output(self, file):
        file.write(self.data)
