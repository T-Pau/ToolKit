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

    def __init__(self, character_width: int, character_height: int, filename: str|None = None, image: Image.Image|None = None, width: int|None = None, height: int|None = None, palette: Palette|None = None, additional_palette:dict[int|str, int | None] | list[int|str|list[int|str]]|None = None, pixel_size:PaletteImage.PixelSize|None = None):
        """Initialize CharacterImage.
        
        Arguments:
            character_width: width of a character in pixels
            character_height: height of a character in pixels
            filename: filename of image to load
            image: image to use
            width: width of image in characters
            height: height of image in characters
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
        if width is not None:
            width *= character_width
        if height is not None:
            height *= character_height
        self.image = PaletteImage.PaletteImage(filename=filename, image=image, width=width, height=height, palette=self.palette, pixel_size=pixel_size)
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
        
        if index < 0 or index >= self.count:
            raise ValueError(f"invalid character index {index}")
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
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"invalid character coordinates ({x}, {y})")
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
                raise RuntimeError(f"partial hole at {x}, {y}")
            value = None
        self.cache[index] = value
        return value

    def set(self, index: int, value: bytes):
        """Set character at given index.

        Arguments:
            index: index of character to set
            value: bytes of character
        
        Raises:
            ValueError: if index is out of bounds or value has invalid size
        """

        if index < 0 or index >= self.count:
            raise ValueError(f"invalid character index {index}")
        x = index % self.width
        y = index // self.width
        self.set_xy(x, y, value)
    
    def set_xy(self, x: int, y: int, value: bytes):
        """Set character at given coordinates.

        Arguments:
            x: x coordinate of character to set
            y: y coordinate of character to set
            value: bytes of character
        
        Raises:
            ValueError: if coordinates are out of bounds or value has invalid size
        """

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"invalid coordinates ({x}, {y})")
        if len(value) != self.character_size:
            raise ValueError(f"invalid character size {len(value)}, expected {self.character_size}")

        index = x + y * self.width
        if index in self.cache and self.cache[index] == value:
            return
        self.cache[index] = value

        i = 0
        image_x = x * self.character_width
        image_y = y * self.character_height
        for yy in range(self.character_height):
            for xx in range(0, self.character_width, self.pixels_per_byte):
                byte = value[i]
                i += 1
                for pixel in range(0, self.pixels_per_byte):
                    color = (byte >> (8 - (pixel + 1) * self.pixel_width)) & ((1 << self.pixel_width) - 1)
                    self.image.set(image_x + xx + pixel, image_y + yy, color)
    