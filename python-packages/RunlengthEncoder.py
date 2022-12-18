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


class RunlengthEncoder:
    class State(enum.Enum):
        empty = enum.auto()
        char = enum.auto()
        skip = enum.auto()

    def __init__(self):
        self.compressed = b""
        self.code_runlength = 0xff
        self.code_skip = 0xfe
        self.state = RunlengthEncoder.State.empty
        self.length = 0
        self.last_byte = -1

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
            if self.length == 255:
                self.end_run()

    def skip(self, amount):
        self.set_state(RunlengthEncoder.State.skip)
        self.length += amount

    def end(self):
        if self.state == RunlengthEncoder.State.char:
            self.set_state(RunlengthEncoder.State.empty)
        self.output(self.code_runlength)
        self.output(0)
        result = self.compressed
        self.compressed = b""
        return result

    def set_state(self, state):
        if self.state == state:
            return
        if self.state == RunlengthEncoder.State.char:
            self.end_run()
        elif self.state == RunlengthEncoder.State.skip:
            self.end_skip()
        self.state = state
        self.last_byte = -1
        self.length = 0

    def end_run(self):
        if self.state != RunlengthEncoder.State.char:
            return
        if self.length > 2 or self.last_byte == self.code_runlength or self.last_byte == self.code_skip:
            self.output(self.code_runlength)
            self.output(self.length)
            self.output(self.last_byte)
        else:
            for i in range(self.length):
                self.output(self.last_byte)
        self.empty()

    def end_skip(self):
        if self.state != RunlengthEncoder.State.skip:
            return
        while self.length > 255:
            self.output(self.code_skip)
            self.output(255)
            self.length -= 255
        if self.length > 0:
            self.output(self.code_skip)
            self.output(self.length)
        self.empty()

    def empty(self):
        self.length = 0
        self.last_byte = -1

    def output(self, byte):
        if type(byte) is bytes:
            self.compressed += byte
        else:
            self.compressed += byte.to_bytes(1, byteorder="little")
