from copy import copy
from PIL import Image

"""
  PaletteImage -- convert image to palette mode
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

from collections import namedtuple

PixelSize = namedtuple("PixelSize", "x y")

class PaletteImage:
    def __init__(self, filename, palette, pixel_size=PixelSize(1,1)):
        self.palette = copy(palette)
        self.filename = filename
        self.pixel_size = pixel_size
        self.image = Image.open(filename)
        if pixel_size.x < 1 or pixel_size.y < 1:
            raise RuntimeError(f"invalid pixel size {pixel_size} at {self.filename}")
        if self.image.width % self.pixel_size.x != 0:
            raise RuntimeError(f"image width {self.image.width} is not multiple of pixel size {self.pixel_size.x} at {self.filename}")
        if self.image.width % self.pixel_size.x != 0:
            raise RuntimeError(f"image height {self.image.height} is not multiple of pixel size {self.pixel_size.y} at {self.filename}")
        self.width = self.image.width // self.pixel_size.x
        self.height = self.image.height // self.pixel_size.y

    def get(self, x, y):
        pixel = None
        for sub_y in range(self.pixel_size.y):
            for sub_x in range(self.pixel_size.x):
                sub_pixel = self.image.getpixel((x * self.pixel_size.x + sub_x, y * self.pixel_size.y + sub_y))
                if pixel is None:
                    pixel = sub_pixel
                elif pixel != sub_pixel:
                    raise RuntimeError(f"non-uniform logical pixel at {self.filename}:({x},{y})")
        alpha = pixel[3] if len(pixel) > 3 else 255
        if alpha == 0:
            color = 0xff000000
        else:
            color = (255-alpha) << 24 | pixel[0] << 16 | pixel[1] << 8 | pixel[2]
        if color in self.palette:
            return self.palette[color]
        else:
            raise RuntimeError(f"invalid color {pixel} at {self.filename}:({x},{y})")
