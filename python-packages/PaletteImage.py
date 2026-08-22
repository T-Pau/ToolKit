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

from FilePositionException import FilePositionException
from Palette import Palette

PixelSize = namedtuple("PixelSize", "x y")
"""Size of logical pixels.

Attributes:
    x: Width of logical pixels.
    y: Height of logical pixels.
"""

class SliceSpecification:
    """Specification of a slice of a logical image."""

    class Axis:
        """Specification of a slice of a logical image along one axis."""

        def __init__(self, size: int, margin_before: int, margin_after: int|None, spacing: int) -> None:
            """Initialize Axis.

            Args:
                size: Size of slice along axis.
                margin_before: Margin before first slice along axis.
                margin_after: Margin after last slice along axis, if None, margin is not checked.
                spacing: Spacing between slices along axis.
            """
            self.size = size
            self.margin_before = margin_before
            self.margin_after = margin_after
            self.spacing = spacing

        def get_count(self, total_size: int) -> int|None:
            """Return number of slices along axis.

            Args:
                total_size: Total size along axis.

            Returns:
                Number of slices along axis.
            """

            total_size -= self.margin_before
            if self.margin_after is not None:
                total_size -= self.margin_after
            if total_size < self.size:
                return None

            count = (total_size + self.spacing) // (self.size + self.spacing)
            if self.margin_after is not None:
                if self.margin_after != total_size - self.size * count + self.spacing * (count - 1):
                    return None
                
            return count

    def __init__(self, width: int, height: int, left_margin: int, top_margin: int, right_margin: int|None, bottom_margin: int|None, x_spacing: int, y_spacing: int) -> None:
        """Initialize SliceSpecification.

        Args:
            left_margin: Left margin before first slice.
            top_margin: Top margin before first slice.
            right_margin: Right margin after last slice, if None, right margin is not checked.
            bottom_margin: Bottom margin after last slice, if None, bottom margin is not checked.
            x_spacing: Horizontal spacing between slices.
            y_spacing: Vertical spacing between slices.
        """
        self.x_axis = self.Axis(width, left_margin, right_margin, x_spacing)
        self.y_axis = self.Axis(height, top_margin, bottom_margin, y_spacing)

    def get_count(self) -> tuple[int, int]:
        """Return number of slices in x and y direction.

        Returns:
            Number of slices in x and y direction.
        """

        count_x = self.x_axis.get_count(self.x_axis.size)
        count_y = self.y_axis.get_count(self.y_axis.size)
        if count_x is None or count_y is None:
            raise ValueError("invalid slice specification")
        return count_x, count_y


class LogicalImage:
    """A logical image, either a PaletteImage or a Window into one."""

    def __init__(self) -> None:
        """Initialize LogicalImage."""

        self.width = 0
        self.height = 0

    @property
    def filename(self) -> str|None:
        """Return filename of image, if any."""
        raise NotImplementedError()

    def get(self, x: int, y: int) -> int | None:
        """Get palette index of logical pixel at (x, y).

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.

        Returns:
            Palette index of logical pixel at (x, y).
        
        Raises:
            ValueError: If (x, y) is outside image.
            FilePositionException: If pixel color is not in palette or logical pixel is non-uniform.
        """
        raise NotImplementedError()

    def set(self, x: int, y: int, color: int) -> None:
        """Set logical pixel at (x, y) to color.

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.
            color: Palette index to set logical pixel to.

        Raises:
            ValueError: If (x, y) is outside image or color is not in palette.
        """
        raise NotImplementedError()

    def get_window(self, x_offset: int, y_offset: int, width: int, height: int) -> "LogicalImage":
        """Return a window into the image.

        Args:
            x_offset: X offset of window into image.
            y_offset: Y offset of window into image.
            width: Width of window.
            height: Height of window.

        Returns:
            A window into the image, or the image itself.

        Raises:
            ValueError: If window is larger than image.
        """
        if x_offset == 0 and y_offset == 0 and width == self.width and height == self.height:
            return self
        return Window(self, x_offset, y_offset, width, height)
    

    def slice(self, spec: SliceSpecification) -> "list[LogicalImage]":
        """Slice image into logical images.

        Args:
            spec: Specification of slice.

        Returns:
            List of logical images.
        """

        count_x, count_y = spec.get_count()
        images = []
        for y in range(count_y):
            for x in range(count_x):
                images.append(self.get_window(
                    spec.x_axis.margin_before + x * (spec.x_axis.size + spec.x_axis.spacing),
                    spec.y_axis.margin_before + y * (spec.y_axis.size + spec.y_axis.spacing),
                    spec.x_axis.size,
                    spec.y_axis.size
                ))
        return images

    def _check_coordinates(self, x: int, y: int) -> None:
        """Check whether (x, y) is inside image.

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.

        Raises:
            ValueError: If (x, y) is outside image.
        """

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"invalid coordinates ({x}, {y})")

class PaletteImage(LogicalImage):
    """Convert image to palette indices."""

    def __init__(self, palette: Palette, filename: str|None = None, image:Image.Image|None = None, width: int|None = None, height: int|None = None, pixel_size: PixelSize = PixelSize(1, 1)) -> None:
        """Initialize PaletteImage.

        Args:
            palette: Palette to use.
            filename: Name of file to load image from.
            image: Image to use.
            width: Width of image in logical pixels.
            height: Height of image in logical pixels.
            pixel_size: Size of logical pixels.
        """

        self.palette = copy(palette)
        self._filename = filename
        self.pixel_size = pixel_size

        given = 0
        if filename is not None:
            given += 1
        if image is not None:
            given += 1
        if width is not None:
            if height is None:
                raise RuntimeError(f"height must be given if width is given for PaletteImage")
            given += 1
        elif height is not None:
            raise RuntimeError(f"width must be given if height is given for PaletteImage")
        if given != 1:
            raise RuntimeError(f"exactly one of filename, image, or width and height must be given for PaletteImage")

        if pixel_size.x < 1 or pixel_size.y < 1:
            raise RuntimeError(f"invalid pixel size {pixel_size} at {self.filename}")

        if filename is not None:
            self.image = Image.open(filename)
        elif image is not None:
            self.image = image
        else:
            self.image = Image.new("RGB", (width * pixel_size.x, height * pixel_size.y))

        if self.image.width % self.pixel_size.x != 0 or self.image.height % self.pixel_size.y != 0:
            raise FilePositionException(f"image dimensions ({self.image.width}x{self.image.height}) are not multiple of pixel size {self.pixel_size}", file=self.filename)
        self.width = self.image.width // self.pixel_size.x
        self.height = self.image.height // self.pixel_size.y

    @property
    def filename(self) -> str|None:
        """Return filename of image, if any."""
        return self._filename

    def get(self, x: int, y: int) -> int | None:
        """Get palette index of logical pixel at (x, y).

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.

        Returns:
            Palette index of logical pixel at (x, y).

        Raises:
            ValueError: If (x, y) is outside image.
            FilePositionException: If pixel color is not in palette or logical pixel is non-uniform.
        """

        self._check_coordinates(x, y)
        
        color = None
        for sub_y in range(self.pixel_size.y):
            for sub_x in range(self.pixel_size.x):
                image_x = x * self.pixel_size.x + sub_x
                image_y = y * self.pixel_size.y + sub_y

                try:
                    sub_color = self.palette[self.image.getpixel((image_x, image_y))]
                except Exception as ex:
                    raise FilePositionException(f"{ex}", file=self.filename, position=(image_x, image_y)) from ex
                
                if color is None:
                    color = sub_color
                elif color != sub_color:
                    raise FilePositionException(f"non-uniform logical pixel", file=self.filename, position=(x * self.pixel_size.x, y * self.pixel_size.y), position_end=((x + 1) * self.pixel_size.x - 1, (y + 1) * self.pixel_size.y - 1))
        return color

    def set(self, x: int, y: int, color: int) -> None:
        """Set logical pixel at (x, y) to color.

        Args:
            x: X coordinate of logical pixel.
            y: Y coordinate of logical pixel.
            color: Palette index to set logical pixel to.

        Raises:
            ValueError: If (x, y) is outside image or color is not in palette.
        """

        self._check_coordinates(x, y)
        color = self.palette.get_color(color)

        image_x = x * self.pixel_size.x
        image_y = y * self.pixel_size.y
        for sub_y in range(self.pixel_size.y):
            for sub_x in range(self.pixel_size.x):
                self.image.putpixel((image_x + sub_x, image_y + sub_y), color)

class Window(LogicalImage):
    """A window into a PaletteImage."""

    def __init__(self, image: LogicalImage, x_offset: int, y_offset: int, width: int, height: int) -> None:
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
        elif isinstance(image, PaletteImage):
            self.image = image
            self.x_offset = x_offset
            self.y_offset = y_offset
            self.width = image.width
            self.height = image.height
        else:
            raise ValueError("image must be a Window or PaletteImage")

        if width is not None:
            self.width = width
        else:
            self.width = self.width - self.x_offset
        if height is not None:
            self.height = height
        else:
            self.height = self.height - self.y_offset

        if self.x_offset < 0 or self.x_offset + self.width > self.image.width or self.y_offset < 0 or self.y_offset + self.height > self.image.height:
            raise ValueError("window larger than image")

    @property
    def filename(self) -> str|None:
        """Return filename of image, if any."""
        return self.image.filename

    def get(self, x: int, y: int) -> int | None:
        """Get palette index of logical pixel at (x, y) in window.

        Args:
            x: X coordinate of logical pixel in window.
            y: Y coordinate of logical pixel in window.

        Returns:
            Palette index of logical pixel at (x, y) in window.
        
        Raises:
            ValueError: If (x, y) is outside window.
            FilePositionException: If pixel color is not in palette or logical pixel is non-uniform.
        """
        
        self._check_coordinates(x, y)
        return self.image.get(self.x_offset + x, self.y_offset + y)

    def set(self, x: int, y: int, color: int) -> None:
        """Set logical pixel at (x, y) to color.

        Args:
            x: X coordinate of logical pixel in window.
            y: Y coordinate of logical pixel in window.
            color: Palette index to set logical pixel to.

        Raises:
            ValueError: If (x, y) is outside window or color is not in palette.
        """
        self._check_coordinates(x, y)
        self.image.set(self.x_offset + x, self.y_offset + y, color)

