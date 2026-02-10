# CharacterImage -- convert image to characters
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

from copy import copy
from PIL import Image

from Palette import Palette
import PaletteImage


class CharacterImage:
    """Access characters from an image."""

    default_palette = Palette({
        0x00000000: 1,
        0x00ffffff: 0,
        0xff000000: 0,
        0x80000000: 0,
        0x0040ff40: None,
    })

    def __init__(self, character_width: int, character_height: int, filename: str|None = None, image: Image.Image|None = None, palette: Palette|None = None, additional_palette:dict[int|str, int | None] | list[int|str|list[int|str]]|None = None, pixel_size:PaletteImage.PixelSize|None = None):
        """Initialize CharacterImage.
        
        Arguments:
            character_width: width of a character in pixels
            character_height: height of a character in pixels
            filename: filename of image to load
            image: image to use
            palette: Palette to use
            additional_palette: additional colors to add to palette
            pixel_size: size of logical pixels
        """

        if pixel_size is None:
            pixel_size = PaletteImage.PixelSize(1, 1)
        if palette is None:
            palette = self.default_palette
        self.palette = copy(palette)
        if additional_palette is not None:
            self.palette.add_colors(additional_palette)
        self.pixel_width = palette.bit_length()
        self.image = PaletteImage.PaletteImage(filename=filename, image=image, palette=self.palette, pixel_size=pixel_size)
        self.character_width = character_width
        self.character_height = character_height
        if self.pixel_width not in (1, 2, 4, 8):
            raise RuntimeError(f"unsupported pixel width {self.pixel_width}")
        if self.character_width % (8/self.pixel_width) != 0:
            raise RuntimeError("character doesn't fit into bytes evenly")
        self.pixels_per_byte = 8 // self.pixel_width
        if self.image.width % self.character_width != 0:
            raise RuntimeError(f"image width not multiple of character width")
        if self.image.height % self.character_height != 0:
            raise RuntimeError(f"image height not multiple of character height")
        self.width = self.image.width // self.character_width
        self.height = self.image.height // self.character_height
        self.count = self.width * self.height
        self.character_size = self.character_width // self.pixels_per_byte * self.character_height
        self.cache = {}

    def get(self, index: int) -> bytes|None:
        """Get character at given index.
        
        Arguments:
            index: index of character to get
        Returns:
            bytes of character, or None if character is a hole
        """
        
        if index in self.cache:
            return self.cache[index]
        return self.get_xy(index % self.width, index // self.width)

    def get_xy(self, x: int, y: int) -> bytes|None:
        """Get character at given coordinates.

        Arguments:
            x: x coordinate of character to get
            y: y coordinate of character to get
        Returns:
            bytes of character, or None if character is a hole
        """
        
        index = x + y * self.width
        if index in self.cache:
            return self.cache[index]

        y *= self.character_height
        x *= self.character_width
        value = b""
        got_pixel = False
        got_hole = False
        for yy in range(y, y + self.character_height):
            for xx in range(x, x + self.character_width, self.pixels_per_byte):
                byte = 0
                for pixel in range(0, self.pixels_per_byte):
                    color = self.image.get(xx + pixel, yy)
                    if color is None:
                        got_hole = True
                    else:
                        got_pixel = True
                        byte |= color << (8 - (pixel + 1) * self.pixel_width)
                value += byte.to_bytes(1, byteorder="little")
        if got_hole:
            if got_pixel:
                raise RuntimeError("partial hole at {x}, {y}")
            value = None
        self.cache[index] = value
        return value
