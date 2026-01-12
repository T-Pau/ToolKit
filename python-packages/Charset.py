
# Charset -- manage character set
# Copyright (C) Dieter Baron
#
# The author can be contacted at <dillo@tpau.group>.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2. The names of the authors may not be used to endorse or promote
#     products derived from this software without specific prior
#     written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



class Charset:
    """Character set."""

    def __init__(self, size: int, empty: bytes, enable_pairs: bool = False):
        """Initialize Charset.
        
        Arguments:
            size: number of characters in character set
            empty: byte sequence representing an empty character
            enable_pairs: whether to enable adding character pairs
        """

        self.by_index: dict[int, bytes] = dict()
        self.by_value: dict[bytes, list[int]] = dict()
        self.next_index: int = 0
        self.size = size
        self.empty = empty
        self.enable_pairs = enable_pairs

    def add(self, value: bytes) -> int:
        """Add character at next free index.
        
        Arguments:
            value: byte sequence representing character to add
        Returns:
            index of added character
        """

        if value in self.by_value:
            return self.by_value[value][0]
        else:
            index = self.get_next_index()
            self.add_with_index(value, index)
            return index

    def add_pair(self, value1: bytes, value2: bytes, offset: int | None = None) -> int:
        """Add character pair at next free index pair.

        Arguments:
            value1: byte sequence representing first character to add
            value2: byte sequence representing second character to add
            offset: offset between first and second character indices
        Returns:
            index of first added character
        """
        
        if offset is None:
            offset = self.size // 2

        if value1 in self.by_value:
            for index in self.by_value[value1]:
                if value2 in self.by_value and index + offset in self.by_value[value2]:
                    return index
        if value1 in self.by_value:
            for index in self.by_value[value1]:
                if not index + offset in self.by_index:
                    self.add_with_index(value2, index + offset)
                    return index
        index = self.get_next_index_pair(offset)
        self.add_with_index(value1, index)
        self.add_with_index(value2, index + offset)
        return index

    def add_with_index(self, value: bytes, index: int):
        """Add character at given index.

        Arguments:
            value: byte sequence representing character to add
            index: index at which to add character
        """

        if index in self.by_index:
            raise RuntimeError(f"character {index} already set")
        else:
            self.by_index[index] = value
            if value not in self.by_value:
                self.by_value[value] = []
            self.by_value[value].append(index)

    def get_next_index(self) -> int:
        while self.next_index in self.by_index:
            if self.next_index >= self.size - 1:
                raise RuntimeError("out of characters")
            self.next_index += 1
        return self.next_index

    def get_next_index_pair(self, offset: int) -> int:
        if self.next_index < self.size - offset:
            for index in range(self.next_index, self.size - offset):
                if index not in self.by_index and index + offset not in self.by_index:
                    return index
        raise RuntimeError("out of characters")

    def get_value(self, index: int) -> bytes:
        """Get character at given index.

        Arguments:
            index: index of character to get
        Returns:
            byte sequence representing character at given index
        """
        if index in self.by_index:
            return self.by_index[index]
        else:
            return self.empty

    @property
    def max_index(self) -> int:
        """Maximum used character index."""
        return max(self.by_index, key=int)

    @property
    def character_count(self) -> int:
        """Number of used characters."""
        return len(self.by_index)

    def get_bytes(self, full: bool = False):
        """Get character set as bytes.

        Arguments:
            full: whether to include all characters or only up to the last used one
        Returns:
            bytes representing the character set
        """
        end = self.size if full else self.max_index + 1
        bytes_array = b""
        for index in range(end):
            value = self.get_value(index)
            for byte in value:
                bytes_array += byte.to_bytes(1, byteorder="little")
        return bytes_array
