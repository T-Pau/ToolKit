"""
  CharacterImage -- convert image to characters
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


import PaletteImage


class CharacterImage:
    palette = {
        0x00000000: 1,
        0x00ffffff: 0,
        0xff000000: 0,
        0x80000000: 0,
        0x0040ff40: -1
    }

    def __init__(self, filename, character_width, character_height, additional_palette=None):
        if additional_palette is not None:
            for color, index in additional_palette.items():
                self.palette[color] = index
        self.image = PaletteImage.PaletteImage(filename, self.palette)
        self.character_width = character_width
        self.character_height = character_height
        if self.character_width % 8 != 0:
            raise RuntimeError("character width not multiple of 8")
        if self.image.width % self.character_width != 0:
            raise RuntimeError(f"image width not multiple of character width")
        if self.image.height % self.character_height != 0:
            raise RuntimeError(f"image height not multiple of character height")
        self.width = self.image.width // self.character_width
        self.height = self.image.height // self.character_height
        self.count = self.width * self.height
        self.character_size = self.character_width // 8 * self.character_height
        self.cache = {}

    def get(self, index):
        if index in self.cache:
            return self.cache[index]
        return self.get_xy(index % self.width, index // self.width)

    def get_xy(self, x, y):
        index = x + y * self.width
        if index in self.cache:
            return self.cache[index]

        y *= self.character_height
        x *= self.character_width
        value = b""
        i = 0
        got_pixel = False
        got_hole = False
        for yy in range(y, y + self.character_height):
            for xx in range(x, x + self.character_width, 8):
                byte = 0
                for bit in range(0, 8):
                    pixel = self.image.get(xx + bit, yy)
                    if pixel == -1:
                        got_hole = True
                    else:
                        got_pixel = True
                        byte |= self.image.get(xx + bit, yy) << (7 - bit)
                value += byte.to_bytes(1, byteorder="little")
                i += 1
        if got_hole:
            if got_pixel:
                raise RuntimeError("partial hole at {x}, {y}")
            value = None
        self.cache[index] = value
        return value
