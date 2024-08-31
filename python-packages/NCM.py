"""
  NCM -- convert images to Nibble Color Mode
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

from PIL import Image


class NCM:
    def __init__(self, filename, palette, char_width=16, char_height=8, fill_color=0):
        # TODO: check char_width <= 16, char_height <= 8
        # TODO: check image.width % char_width == 0, same for height
        self.image = Image.open(filename)
        self.palette = palette
        self.fill_color = fill_color
        self.char_width = char_width
        self.char_height = char_height
        self.width = self.image.width // char_width
        self.height = self.image.height // char_height

    def get(self, x, y):
        data = b""
        for yy in range(0, 8):
            b = 0
            for xx in range(0, 16):
                color = self.fill_color
                if xx < self.char_width and yy < self.char_height:
                    color = self.rgb2index(self.image.getpixel((x * self.char_width + xx, y * self.char_height + yy)))
                if xx % 2 == 0:
                    b = color
                else:
                    b = b | (color << 4)
                    data += b.to_bytes(1, byteorder="little")
        return data

    def rgb2index(self, rgb):
        return self.palette[rgb[0] << 16 | rgb[1] << 8 | rgb[2]]
