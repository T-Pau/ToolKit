import MessageHandler
import Palette
import PaletteImage
class ColorStore:
    def __init__(self, formatter, per_cell=True):
        self.formatter = formatter
        self.per_cell = per_cell

class Constraint:
    def __init__(self, check, message):
        self.check = check
        self.message = message

class Layout:
    def __init__(self, cell_width: int , cell_height: int, cell_colors: int, common_colors: int|None, palette: Palette.Palette, color_stores: dict[str, ColorStore], pixel_size: PaletteImage.PixelSize|None = None, cell_constraints: Constraint|None = None, global_constraints:list[Constraint]|None = None):
        if cell_colors < 1:
            raise ValueError("cell colors must be at least 1")
        if common_colors is not None and common_colors < 0:
            raise ValueError("common colors cannot be negative")
        if common_colors is not None and common_colors > cell_colors:
            raise ValueError("more common colors than cell colors")
        if cell_width < 1 or cell_height < 1:
            raise ValueError("cell dimensions must be at least 1")
        if common_colors is not None and common_colors > 1:
            raise ValueError("more than one common color not supported yet")
        for name in color_stores:
            if name == "bitmap":
                raise ValueError("bitmap is reserved component name")

        if common_colors == 0:
            common_colors = None
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.cell_colors = cell_colors
        self.common_colors = common_colors
        self.palette = palette
        self.pixel_size = pixel_size
        self.cell_constraints = cell_constraints
        self.global_constraints = global_constraints
        self.color_stores = color_stores


c64_hires = Layout(8, 8, 2, 0, Palette.c64, {
    "screen": ColorStore(lambda colors: colors[1] << 4 | colors[0])
})
c64_multicolor = Layout(4, 8, 4, 1, Palette.c64, {
    "background": ColorStore(lambda colors: colors[0], per_cell=False),
    "screen": ColorStore(lambda colors: colors[1] << 4 | colors[2]),
    "color": ColorStore(lambda colors: colors[3])
}, PaletteImage.PixelSize(2,1))
spectrum = Layout(8, 8, 2, 0, Palette.spectrum, {
    "attributes": ColorStore(lambda colors: colors[1] << 4 | colors[0]) # TODO: bright bit
}, cell_constraints=Constraint(lambda cell: cell.colors[0] & 0x8 == cell.colors[1] & 0x8, "different brightness attributes"))

layouts = {
    "c64-hires": c64_hires,
    "c64-multicolor": c64_multicolor,
    "spectrum": spectrum
}

class Cell:
    def __init__(self, pixels: list[int], colors: list[int]):
        self.pixels = pixels
        self.colors = colors

        for pixel in pixels:
            if pixel >= len(colors):
                raise RuntimeError(f"pixel value {pixel:06x} larger than palette size")

    def add_color(self, color: int) -> None:
        self.colors.append(color)

    def num_colors(self) -> int:
        return len(self.colors)

    def recolor(self, color: int, new_index: int) -> None:
        try:
            old_index = self.colors.index(color)
        except ValueError:
            old_index = self.num_colors()
            self.colors.append(color)

        if old_index == new_index:
            return

        x = { old_index: new_index }
        if new_index < old_index:
            for i in range(new_index, old_index):
                x[i] = i + 1
            self.colors = self.colors[:new_index] + [color] + self.colors[new_index:old_index] + self.colors[old_index+1:]
        else:
            for i in range(old_index + 1, new_index + 1):
                x[i] = i - 1
            self.colors = self.colors[:old_index] + self.colors[old_index+1:new_index+1] + [color] + self.colors[new_index+1:]

        for pixel_index in range(len(self.pixels)):
            if self.pixels[pixel_index] in x:
                self.pixels[pixel_index] = x[self.pixels[pixel_index]]

class CellImage:
    def __init__(self, filename: str, layout: Layout, unused_colors: list[int]|None = None):
        errors = []
        pixel_size = layout.pixel_size
        if pixel_size is None:
            pixel_size = PaletteImage.PixelSize(1, 1)
        self.image = PaletteImage.PaletteImage(layout.palette, filename, pixel_size=pixel_size)
        self.cell_width = layout.cell_width
        self.cell_height = layout.cell_height
        if self.image.width % self.cell_width != 0 or self.image.height % self.cell_height != 0:
            raise RuntimeError(f"image dimensions ({self.image.width}x{self.image.height}) not multiple of cell size ({self.cell_width}x{self.cell_height})")

        self.width = self.image.width // self.cell_width
        self.height = self.image.height // self.cell_height
        self.cells: list[Cell] = []

        possible_common_colors = None
        histogram = [0] * len(layout.palette)

        ok = True

        for cell_y in range(self.height):
            for cell_x in range(self.width):
                cell = self.compute_cell(cell_x, cell_y)
                if cell is None:
                    ok = False
                    cell = Cell([], [])
                self.cells.append(cell)
                if cell.num_colors() > layout.cell_colors:
                    MessageHandler.error(f"too many colors in cell", file=filename, position=self._cell_to_image_coordinates(cell_x, cell_y))
                    ok = False
                    continue

                if layout.common_colors is not None and cell.num_colors() == layout.cell_colors:
                    if possible_common_colors is None:
                        possible_common_colors = set(cell.colors)
                    else:
                        possible_common_colors &= set(cell.colors)
                    for color in cell.colors:
                        histogram[color] += 1
                if layout.cell_constraints is not None:
                    if not layout.cell_constraints.check(cell):
                        MessageHandler.error(f"{layout.cell_constraints.message} in cell", file=filename, position=self._cell_to_image_coordinates(cell_x, cell_y), position_end=self._cell_to_image_coordinates(cell_x, cell_y, end=True))
                        ok = False

        if layout.common_colors is not None:
            if possible_common_colors is None or len(possible_common_colors) < layout.common_colors:
                best_color = histogram.index(max(histogram))
                invalid_cells = []
                for index, cell in enumerate(self.cells):
                    if cell.num_colors() == layout.cell_colors:
                        if best_color not in cell.colors:
                            invalid_cells.append(index)
                
                MessageHandler.error(f"not enough common colors found; best candidate is color {best_color} missing in {len(invalid_cells)} cells", file=filename)
                for cell in invalid_cells:
                    MessageHandler.error(f"too many non-common colors in cell", file=filename, position=self._cell_index_to_image_coordinates(cell), position_end=self._cell_index_to_image_coordinates(cell, end=True))
                raise RuntimeError()
            common_colors_list = list(possible_common_colors)[:layout.common_colors]
            for cell in self.cells:
                for i, color in enumerate(common_colors_list):
                    cell.recolor(color, i)
        
        for cell in self.cells:
            for i in range(cell.num_colors(), layout.cell_colors):
                if unused_colors is not None and i < len(unused_colors):
                    color = unused_colors[i]
                else:
                    color = 0
                cell.add_color(color)

        if layout.global_constraints is not None:
            for constraint in layout.global_constraints:
                if not constraint.check(self):
                    MessageHandler.error(f"{constraint.message}", file=filename)
                    ok = False
        if not ok:
            raise RuntimeError()

        self.components = {}
        for name, store in layout.color_stores.items():
            if store.per_cell:
                values = b""
                for cell in self.cells:
                    values += store.formatter(cell.colors).to_bytes(1, byteorder="little")
                self.components[name] = values
            else:
                self.components[name] = store.formatter(self.cells[0].colors[0:layout.common_colors])
        
        bitmap = b""
        bits_per_pixel = (layout.cell_colors - 1).bit_length()
        pixels_per_byte = 8 // bits_per_pixel
        for cell in self.cells:
            for y in range(self.cell_height):
                for x in range(0, self.cell_width, pixels_per_byte):
                    byte = 0
                    for pixel in range(pixels_per_byte):
                        color_index = cell.pixels[y * self.cell_width + x + pixel]
                        byte |= color_index << (8 - (pixel + 1) * bits_per_pixel)
                    bitmap += byte.to_bytes(1, byteorder="little")
        self.components["bitmap"] = bitmap

    def compute_cell(self, cell_x: int, cell_y: int) -> Cell|None:
        pixels = []
        colors = []
        for y in range(self.cell_height):
            for x in range(self.cell_width):
                image_x = cell_x * self.cell_width + x
                image_y = cell_y * self.cell_height + y
                try:
                    color = self.image.get(image_x, image_y)
                except Exception as ex:
                    MessageHandler.error_from_exception(ex, omit_empty=True)
                    return None
                try:
                    index = colors.index(color)
                except ValueError:
                    index = len(colors)
                    colors.append(color)
                pixels.append(index)
        return Cell(pixels, colors)
    
    def component_names(self) -> list[str]:
        return list(self.components.keys())

    def get(self, name: str) -> bytes|int:
        if name in self.components:
            return self.components[name]
        else:
            raise RuntimeError(f"unknown component '{name}'")

    def is_global(self, name):
        if name in self.components:
            return self.components[name] is not bytes
        else:
            raise RuntimeError(f"unknown component '{name}'")

    def _cell_index_to_image_coordinates(self, index: int, end: bool = False) -> tuple[int, int]:
        """Convert cell index to image coordinates.
        Args:
            index: Index of cell.

        Returns:
            Image coordinates as a tuple (x, y).
        """
        cell_x = index % self.width
        cell_y = index // self.width
        return self._cell_to_image_coordinates(cell_x, cell_y, end)
    
    def _cell_to_image_coordinates(self, cell_x: int, cell_y: int, end: bool = False) -> tuple[int, int]:
        """Convert cell coordinates to image coordinates.
        Args:
            cell_x: X coordinate of cell.
            cell_y: Y coordinate of cell.

        Returns:
            Image coordinates as a tuple (x, y).
        """
        image_x = cell_x * self.cell_width * self.image.pixel_size.x
        image_y = cell_y * self.cell_height * self.image.pixel_size.y
        if end:
            image_x += (self.cell_width * self.image.pixel_size.x) - 1
            image_y += (self.cell_height * self.image.pixel_size.y) - 1
        return (image_x, image_y)
