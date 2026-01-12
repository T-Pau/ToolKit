from typing import IO

class Buffer:
    """Create binary data incrementally."""

    def __init__(self, padding: int = 0, byteorder: str = "little") -> None:
        """Initialize buffer.
        
        Arguments:
            padding: byte value to use for padding
            byteorder: byte order to use for multi-byte values
        """

        self.data = b""
        self.padding = padding
        self.byteorder = byteorder
    
    def add_byte(self, byte: int, count: int = 1) -> None:
        """Add one or more bytes to buffer.
        
        Arguments:
            byte: byte value to add
            count: number of times to add byte
        """

        self.data += byte.to_bytes(1, byteorder="little") * count
    
    def add_data(self, data: bytes | str, length: int = 0, padding: int | None = None) -> None:
        """Add data to buffer, with optional padding.

        Arguments:
            data: data to add (bytes or string)
            length: pad data to this length if it is shorter
            padding: byte value to use for padding
        """

        if padding is None:
            padding = self.padding
        if type(data) is str:
            data = bytearray(data.upper(), "utf-8")
        self.data += data
        if len(data) < length:
            self.data += padding.to_bytes(1, byteorder="little") * (length - len(data))
    
    def add_word(self, word: int, byteorder: str | None = None) -> None:
        """Add a word (2 bytes) to buffer.
        
        Arguments:
            word: word value to add
            byteorder: override default byte order
        """
        self.add_int(word, 2, byteorder)

    def add_long(self, value: int, byteorder: str | None = None) -> None:
        """Add a long (4 bytes) to buffer.

        Arguments:
            value: long value to add
            byteorder: override default byte order
        """
        self.add_int(value, 4, byteorder)

    def add_int(self, value: int, size: int, byteorder: str | None = None) -> None:
        """Add an integer of given size to buffer.

        Arguments:
            value: integer value to add
            size: size of integer in bytes
            byteorder: override default byte order
        """
        if byteorder is None:
            byteorder = self.byteorder
        self.data += value.to_bytes(size, byteorder=byteorder)

    def add_zeros(self, length: int) -> None:
        """Add given number of zero bytes to buffer.

        Arguments:
            length: number of zero bytes to add
        """

        self.data += b"\x00" * length

    def clear(self) -> None:
        """Clear buffer contents."""
        self.data = b""

    def pad(self, length: int, padding: int | None = None) -> None:
        """Pad buffer to given length.

        Arguments:
            length: length of buffer after padding
            padding: padding byte
        """
        if padding is None:
            padding = self.padding
        if len(self.data) < length:
            self.data += padding.to_bytes(1, byteorder="little") * (length - len(self.data))

    def output(self, file: "IO[bytes]") -> None:
        """Write buffer contents to file.

        Arguments:
            file: file object to write to
        """

        file.write(self.data)
