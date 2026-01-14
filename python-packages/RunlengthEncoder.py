"""
  RunlengthEncoder -- run length encoder with skip support
  Copyright (C) Dieter Baron

  The author can be contacted at <dillo@tpau.group>.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:
  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. The names of the authors may not be used to endorse or promote
     products derived from this software without specific prior
     written permission.

  THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS
  OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import enum
from typing import Any, Iterable

class Trim(enum.Enum):
    none = "none"
    leading = "leading"
    trailing = "trailing"
    both = "both"


class _RunlengthEncoder:
    """Base class for runlength encoders with skip support."""
    class State(enum.Enum):
        empty = enum.auto()
        char = enum.auto()
        skip = enum.auto()

    def __init__(self, trim: Trim = Trim.trailing) -> None:
        """Initialize runlength encoder.
        
        Arguments:
            trim: Specifies whether leading and/or trailing skips should be trimmed.
        """

        self.code_runlength = 0x80
        self.code_skip = 0xc0
        self.trim = trim
        self.state = _RunlengthEncoder.State.empty
        self.last_element = None
        self.state = _RunlengthEncoder.State.empty
        self.length = 0
        self.literal = []

    def _reset(self) -> None:
        self.last_element = None
        self.state = _RunlengthEncoder.State.empty
        self.length = 0
        self.literal = []

    def skip(self, amount: int) -> None:
        """Skip the specified number of elements.
        
        Arguments:
            amount: Number of elements to skip.
        """

        if amount == 0:
            return
        if self.state == _RunlengthEncoder.State.empty and (self.trim == Trim.leading or self.trim == Trim.both):
            return
        self._set_state(_RunlengthEncoder.State.skip)
        self.length += amount

    def _add_element(self, element: Any) -> None:
        self._set_state(_RunlengthEncoder.State.char)
        if element != self.last_element:
            if self.last_element is not None:
                self._end_run()
            self.last_element = element
            self.length = 1
        else:
            self.length += 1

    def _add_multiple_elements(self, elements: Iterable) -> None:
        for element in elements:
            self._add_element(element)

    def _end(self):
        if self.state == _RunlengthEncoder.State.char or (self.state == _RunlengthEncoder.State.skip and self.trim != Trim.trailing and self.trim != Trim.both):
            self._set_state(_RunlengthEncoder.State.empty)
        self._encode_end()
    
    def _set_state(self, state: State) -> None:
        if self.state == state:
            return
        if self.state == _RunlengthEncoder.State.char:
            self._end_run()
        elif self.state == _RunlengthEncoder.State.skip:
            self._end_skip()
        self.state = state
        self.last_element = None
        self.length = 0

    def _end_run(self) -> None:
        if self.state != _RunlengthEncoder.State.char:
            return
        if self.length > 2:
            self._encode_literal()
            self._encode_run(self.length, self.last_element)
        else:
            self.literal.extend([self.last_element] * self.length)
            self._encode_literal()
        self._empty()

    def _end_char(self) -> None:
        if self.state != _RunlengthEncoder.State.char:
            return
        self._end_run()
        self._encode_literal()
        self._empty()

    def _end_skip(self) -> None:
        if self.state != _RunlengthEncoder.State.skip:
            return
        self._encode_skip(self.length)
        self._empty()

    def _empty(self) -> None:
        self.length = 0
        self.last_element = None

    def _encode_literal(self) -> None:
        offset = 0
        while offset + 127 < len(self.literal):
            self._output(127)
            self._output(self.literal[offset:offset+127])
            offset += 127
        if offset < len(self.literal):
            self._output(len(self.literal) - offset)
            self._output(self.literal[offset:])
        self.literal = []

    def _encode_run(self, length: int, element: Any) -> None:
        while length > 0:
            chunk = min(length, 63)
            self._output(self.code_runlength + chunk)
            self._output([element])
            length -= chunk

    def _encode_skip(self, length: int) -> None:
        while length > 0:
            chunk = min(length, 63)
            self._output(self.code_skip + chunk)
            length -= chunk

    def _encode_end(self) -> None:
        self._output(self.code_skip)

    def _output(self, data: int|list) -> None:
        raise NotImplementedError("Subclasses must implement _output method.")


class BinaryRunlengthEncoder(_RunlengthEncoder):
    def __init__(self, trim: Trim = Trim.trailing) -> None:
        super().__init__(trim=trim)
        self.compressed = b""

    def _reset(self) -> None:
        self.compressed = b""

    def add(self, byte: int) -> None:
        super()._add_element(byte)

    def add_bytes(self, data: bytes) -> None:
        super()._add_multiple_elements(data)

    def end(self) -> bytes:
        super()._end()
        result = self.compressed
        self._reset()
        return result

    def _output(self, data: int|list) -> None:
        if type(data) is list:
            self.compressed += bytes(data)
        elif type(data) is int:
            self.compressed += data.to_bytes(1, byteorder="little")
        else:
            raise TypeError("byte must be int or list")


class SymbolRunlengthEncoder(_RunlengthEncoder):
    def __init__(self, trim: Trim = Trim.trailing) -> None:
        super().__init__(trim=trim)
        self.compressed = []

    def _reset(self) -> None:
        super()._reset()
        self.compressed = []

    def add(self, symbol: Any) -> None:
        super()._add_element(symbol)

    def add_list(self, symbols: Iterable) -> None:
        super()._add_multiple_elements(symbols)

    def end(self) -> list:
        super()._end()
        result = self.compressed
        self._reset()
        return result

    def _output(self, data: int|list) -> None:
        if type(data) is list:
            self.compressed += data
        elif type(data) is int:
            self.compressed.append("$%0.2x" % data)
        else:
            raise TypeError("byte must be int or list")
