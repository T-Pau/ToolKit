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
from typing import Any

class Trim(enum.Enum):
    none = "none"
    leading = "leading"
    trailing = "trailing"
    both = "both"


class RunlengthEncoder:
    class State(enum.Enum):
        empty = enum.auto()
        char = enum.auto()
        skip = enum.auto()

    def __init__(self, trim: Trim = Trim.trailing, binary: bool = True) -> None:
        self.binary = binary
        self.compressed = self.empty_string()
        self.literal = self.empty_string()
        self.code_runlength = 0x80
        self.code_skip = 0xc0
        self.state = RunlengthEncoder.State.empty
        self.length = 0
        self.last_byte = None
        self.trim = trim

    def add_bytes(self, data: bytes) -> None:
        for byte in data:
            self.add(byte)

    def add(self, byte: int) -> None:
        self.set_state(RunlengthEncoder.State.char)
        if byte != self.last_byte:
            self.end_run()
            self.last_byte = byte
            self.length = 1
        else:
            self.length += 1

    def skip(self, amount: int) -> None:
        if amount == 0:
            return
        if self.state == RunlengthEncoder.State.empty and (self.trim == Trim.leading or self.trim == Trim.both):
            return
        self.set_state(RunlengthEncoder.State.skip)
        self.length += amount

    def end(self) -> list | bytes:
        if self.state == RunlengthEncoder.State.char or (self.state == RunlengthEncoder.State.skip and self.trim != Trim.trailing and self.trim != Trim.both):
            self.set_state(RunlengthEncoder.State.empty)
        self.encode_end()
        result = self.compressed
        self.compressed = self.empty_string()
        return result

    def set_state(self, state: State) -> None:
        if self.state == state:
            return
        if self.state == RunlengthEncoder.State.char:
            self.end_char()
        elif self.state == RunlengthEncoder.State.skip:
            self.end_skip()
        self.state = state
        self.last_byte = None
        self.length = 0

    def end_run(self) -> None:
        if self.state != RunlengthEncoder.State.char:
            return
        if self.length > 2:
            self.encode_literal(self.literal)
            self.literal = self.empty_string()
            self.encode_run(self.length, self.last_byte)
        else:
            for i in range(self.length):
                self.add_literal(self.last_byte)
        self.empty()

    def end_char(self) -> None:
        if self.state != RunlengthEncoder.State.char:
            return
        self.end_run()
        self.encode_literal(self.literal)
        self.literal = b""
        self.empty()

    def end_skip(self) -> None:
        if self.state != RunlengthEncoder.State.skip:
            return
        self.encode_skip(self.length)
        self.empty()

    def empty(self) -> None:
        self.length = 0
        self.last_byte = None

    def encode_literal(self, data: list | bytes) -> None:
        offset = 0
        while offset + 127 < len(data):
            self.output(127)
            self.output(data[offset:offset+127])
            offset += 127
        if offset < len(data):
            self.output(len(data) - offset)
            self.output(data[offset:])

    def encode_run(self, length: int, byte: Any) -> None:
        while self.length > 63:
            self.output(self.code_runlength + 63)
            self.output(byte)
            self.length -= 63
        if self.length > 0:
            self.output(self.code_runlength + self.length)
            self.output(byte)

    def encode_skip(self, length: int) -> None:
        while length > 63:
            self.output(self.code_skip + 63)
            length -= 63
        if length > 0:
            self.output(self.code_skip + length)

    def encode_end(self) -> None:
        self.output(self.code_skip)

    def output(self, byte: Any) -> None:
        if self.binary:
            if type(byte) is bytes:
                self.compressed += byte
            else:
                self.compressed += byte.to_bytes(1, byteorder="little")
        else:
            if type(byte) is list:
                self.compressed += byte
            else:
                if type(byte) is int:
                    byte = "$%0.2x" % byte
                self.compressed.append(byte)

    def empty_string(self) -> list | bytes:
        if self.binary:
            return b""
        else:
            return []
    
    def add_literal(self, byte):
        if self.binary:
            self.literal += byte.to_bytes(1, byteorder="little")
        else:
            self.literal.append(byte)
