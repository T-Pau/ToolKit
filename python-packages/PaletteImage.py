# PaletteImage -- convert image to palette mode
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

"""This module converts possibly non-square pixels of an image to palette indices.
"""

from copy import copy
from PIL import Image
from collections import namedtuple
from typing import TypeAlias

from Palette import Palette

PixelSize = namedtuple("PixelSize", "x y")
"""Size of logical pixels.

Attributes:
    x: Width of logical pixels.
    y: Height of logical pixels.
"""

class PaletteImage:
    """Convert image to palette indices."""

    def __init__(self, palette: Palette, filename: str|None = None, image:Image.Image|None = None, pixel_size: PixelSize = PixelSize(1, 1)) -> None:
        """Initialize PaletteImage.

        Args:
            filename: Name of file to load image from.
            palette: Palette to use.
            image: Image to use.
            pixel_size: Size of logical pixels.
        """

        self.palette = copy(palette)
        self.filename = filename
        self.pixel_size = pixel_size

        if filename is not None:
            self.image = Image.open(filename)
            if image is not None:
                raise RuntimeError(f"both filename and image given for PaletteImage")
        elif image is not None:
            self.image = image
        else:
            raise RuntimeError(f"neither filename nor image given for PaletteImage")
        
        if pixel_size.x < 1 or pixel_size.y < 1:
            raise RuntimeError(f"invalid pixel size {pixel_size} at {self.filename}")
        if self.image.width % self.pixel_size.x != 0:
            raise RuntimeError(f"image width {self.image.width} is not multiple of pixel size {self.pixel_size.x} at {self.filename}")
        if self.image.width % self.pixel_size.x != 0:
            raise RuntimeError(f"image height {self.image.height} is not multiple of pixel size {self.pixel_size.y} at {self.filename}")
        self.width = self.image.width // self.pixel_size.x
        self.height = self.image.height // self.pixel_size.y

    def get(self, x: int, y: int) -> int | None:
        """Get palette index of logical pixel at (x, y).

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.

        Returns:
            Palette index of logical pixel at (x, y).

        Raises:
            ValueError: If (x, y) is outside image.
            RuntimeError: If pixel color is not in palette or logical pixel is non-uniform.
        """

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"invalid coordinates ({x}, {y})")
        
        color = None
        for sub_y in range(self.pixel_size.y):
            for sub_x in range(self.pixel_size.x):
                image_x = x * self.pixel_size.x + sub_x
                image_y = y * self.pixel_size.y + sub_y

                try:
                    sub_color = self.palette[self.image.getpixel((image_x, image_y))]
                except Exception as ex:
                    raise RuntimeError(f"{ex} at {self.filename}:({image_x},{image_y})")
                
                if color is None:
                    color = sub_color
                elif color != sub_color:
                    raise RuntimeError(f"non-uniform logical pixel at {self.filename}:({image_x},{image_y})")
        return color

class Window:
    """A window into a PaletteImage."""

    def __init__(self, image: "PaletteImage|Window", x_offset: int, y_offset: int, width: int, height: int) -> None:
        """Initialize window.
        
        Args:
            image: Image or window to create window into.
            x_offset: X offset of window into image.
            y_offset: Y offset of window into image.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If window is larger than image.

        """
        if isinstance(image, Window):
            self.image = image.image
            self.x_offset = image.x_offset + x_offset
            self.y_offset = image.y_offset + y_offset
        else:
            self.image = image
            self.x_offset = x_offset
            self.y_offset = y_offset
        self.width = width
        self.height = height

        if self.x_offset < 0 or self.x_offset + self.width > self.image.width or self.y_offset < 0 or self.y_offset + self.height > self.image.height:
            raise ValueError("window larger than image")

    def get(self, x: int, y: int) -> int | None:
        """Get palette index of logical pixel at (x, y) in window.

        Args:
            x: X coordinate of logical pixel in window.
            y: Y coordinate of logical pixel in window.

        Returns:
            Palette index of logical pixel at (x, y) in window.
        
        Raises:
            ValueError: If (x, y) is outside window.
            RuntimeError: If pixel color is not in palette or logical pixel is non-uniform.
        """
        
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"invalid coordinates ({x}, {y})")
        return self.image.get(self.x_offset + x, self.y_offset + y)

LogicalImage: TypeAlias = PaletteImage | Window
"""A logical image, either a PaletteImage or a Window into one."""