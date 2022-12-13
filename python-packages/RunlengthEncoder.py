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


class RunlengthEncoder:
    def __init__(self):
        self.compressed = b""
        self.code_runlength = 0xff
        self.code_skip = 0xfe
        self.last_byte = -1
        self.runlength = 0

    def add_bytes(self, bytes):
        for byte in bytes:
            self.add(byte)

    def add(self, byte):
        if byte != self.last_byte:
            self.end_run()
            self.last_byte = byte
            self.runlength = 1
        else:
            self.runlength += 1
            if self.runlength == 255:
                self.end_run()

    def skip(self, amount):
        if amount == 0:
            return
        self.end_run()
        while amount > 255:
            self.output(self.code_skip)
            self.output(255)
            amount -= 255
        if amount > 0:
            self.output(self.code_skip)
            self.output(amount)

    def end(self):
        self.end_run()
        self.output(self.code_runlength)
        self.output(0)
        result = self.compressed
        self.compressed = b""
        return result

    def end_run(self):
        if self.runlength > 2 or self.last_byte == self.code_runlength or self.last_byte == self.code_skip:
            self.output(self.code_runlength)
            self.output(self.runlength)
            self.output(self.last_byte)
        else:
            for i in range(self.runlength):
                self.output(self.last_byte)
        self.last_byte = -1
        self.runlength = 0

    def output(self, byte):
        if type(byte) is bytes:
            self.compressed += byte
        else:
            self.compressed += byte.to_bytes(1, byteorder="little")
