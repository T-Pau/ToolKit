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

    def __init__(self, trim=Trim.trailing):
        self.compressed = b""
        self.literal = b""
        self.code_runlength = 0x80
        self.code_skip = 0xc0
        self.state = RunlengthEncoder.State.empty
        self.length = 0
        self.last_byte = -1
        self.trim = trim

    def add_bytes(self, data):
        for byte in data:
            self.add(byte)

    def add(self, byte):
        self.set_state(RunlengthEncoder.State.char)
        if byte != self.last_byte:
            self.end_run()
            self.last_byte = byte
            self.length = 1
        else:
            self.length += 1

    def skip(self, amount):
        if amount == 0:
            return
        if self.state == RunlengthEncoder.State.empty and (self.trim == Trim.leading or self.trim == Trim.both):
            return
        self.set_state(RunlengthEncoder.State.skip)
        self.length += amount

    def end(self):
        if self.state == RunlengthEncoder.State.char or (self.state == RunlengthEncoder.State.skip and self.trim != Trim.trailing and self.trim != Trim.both):
            self.set_state(RunlengthEncoder.State.empty)
        self.encode_end()
        result = self.compressed
        self.compressed = b""
        return result

    def set_state(self, state):
        if self.state == state:
            return
        if self.state == RunlengthEncoder.State.char:
            self.end_char()
        elif self.state == RunlengthEncoder.State.skip:
            self.end_skip()
        self.state = state
        self.last_byte = -1
        self.length = 0

    def end_run(self):
        if self.state != RunlengthEncoder.State.char:
            return
        if self.length > 2:
            self.encode_literal(self.literal)
            self.literal = b""
            self.encode_run(self.length, self.last_byte)
        else:
            for i in range(self.length):
                self.literal += self.last_byte.to_bytes(1, byteorder="little")
        self.empty()

    def end_char(self):
        if self.state != RunlengthEncoder.State.char:
            return
        self.end_run()
        self.encode_literal(self.literal)
        self.literal = b""
        self.empty()

    def end_skip(self):
        if self.state != RunlengthEncoder.State.skip:
            return
        self.encode_skip(self.length)
        self.empty()

    def empty(self):
        self.length = 0
        self.last_byte = -1

    def encode_literal(self, data):
        offset = 0
        while offset + 127 < len(data):
            self.output(127)
            self.output(data[offset:offset+127])
            offset += 127
        if offset < len(data):
            self.output(len(data) - offset)
            self.output(data[offset:])

    def encode_run(self, length, byte):
        while self.length > 63:
            self.output(self.code_runlength + 63)
            self.output(self.last_byte)
            self.length -= 63
        if self.length > 0:
            self.output(self.code_runlength + self.length)
            self.output(self.last_byte)

    def encode_skip(self, length):
        while length > 63:
            self.output(self.code_skip + 63)
            length -= 63
        if length > 0:
            self.output(self.code_skip + length)

    def encode_end(self):
        self.output(self.code_skip)

    def output(self, byte):
        if type(byte) is bytes:
            self.compressed += byte
        else:
            self.compressed += byte.to_bytes(1, byteorder="little")
