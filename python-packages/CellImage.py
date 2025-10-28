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
    def __init__(self, cell_width, cell_height, cell_colors, common_colors, palette, color_stores, pixel_size=None, cell_constraints=None, global_constraints=None):
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
    def __init__(self, pixels, colors):
        self.pixels = pixels
        self.colors = colors

        for pixel in pixels:
            if pixel >= len(colors):
                raise RuntimeError(f"pixel value {pixel:06x} larger than palette size")

    def add_color(self, color):
        self.colors.append(color)

    def num_colors(self):
        return len(self.colors)

    def recolor(self, color, new_index):
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
    def __init__(self, filename, layout, unused_colors=None):
        pixel_size = layout.pixel_size
        if pixel_size is None:
            pixel_size = PaletteImage.PixelSize(1, 1)
        self.image = PaletteImage.PaletteImage(filename, layout.palette, pixel_size)
        self.cell_width = layout.cell_width
        self.cell_height = layout.cell_height
        if self.image.width % self.cell_width != 0:
            raise RuntimeError(f"image width not multiple of cell width")
        if self.image.height % self.cell_height != 0:
            raise RuntimeError(f"image height not multiple of cell height")
        common_colors = layout.common_colors
        cell_colors = layout.cell_colors
        if common_colors == 0:
            common_colors = None
        if common_colors is not None and common_colors > cell_colors:
            raise RuntimeError("more common colors than cell colors")
        if common_colors is not None and common_colors > 1:
            raise RuntimeError("more than one common color not supported yet")

        self.width = self.image.width // self.cell_width
        self.height = self.image.height // self.cell_height
        self.cells = []

        possible_common_colors = None

        for cell_y in range(self.height):
            for cell_x in range(self.width):
                cell = self.compute_cell(cell_x, cell_y)
                if cell.num_colors() > cell_colors:
                    raise RuntimeError(f"too many colors in cell ({cell_x},{cell_y})")
                self.cells.append(cell)

                if common_colors is not None and cell.num_colors() == cell_colors:
                    if possible_common_colors is None:
                        possible_common_colors = set(cell.colors)
                    else:
                        possible_common_colors &= set(cell.colors)
                
                if layout.cell_constraints is not None:
                    if not layout.cell_constraints.check(cell):
                        raise RuntimeError(f"{layout.cell_constraints.message} in cell ({cell_x},{cell_y})")
                
        if common_colors is not None:
            if possible_common_colors is None or len(possible_common_colors) < common_colors:
                raise RuntimeError("not enough common colors found")
            common_colors_list = list(possible_common_colors)[:common_colors]
            for cell in self.cells:
                for i, color in enumerate(common_colors_list):
                    cell.recolor(color, i)
        
        for cell in self.cells:
            for i in range(cell.num_colors(), cell_colors):
                if unused_colors is not None and i < len(unused_colors):
                    color = unused_colors[i]
                else:
                    color = 0
                cell.add_color(color)
                

        
        if layout.global_constraints is not None:
            for constraint in layout.global_constraints:
                if not constraint.check(self):
                    raise RuntimeError(f"{constraint.message}")
        
        self.components = {}
        for name, store in layout.color_stores.items():
            if name == "bitmap":
                raise RuntimeError("bitmap is reserved component name")
            if store.per_cell:
                values = b""
                for cell in self.cells:
                    values += store.formatter(cell.colors).to_bytes(1, byteorder="little")
                self.components[name] = values
            else:
                self.components[name] = store.formatter(self.cells[0].colors[0:common_colors])
        
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

    def compute_cell(self, cell_x, cell_y):
        pixels = []
        colors = []
        for y in range(self.cell_height):
            for x in range(self.cell_width):
                color = self.image.get(x + cell_x * self.cell_width, y + cell_y * self.cell_height)
                try:
                    index = colors.index(color)
                except ValueError:
                    index = len(colors)
                    colors.append(color)
                pixels.append(index)
        return Cell(pixels, colors)
    
    def component_names(self):
        return self.components.keys()

    def get(self, name):
        if name in self.components:
            return self.components[name]
        else:
            raise RuntimeError(f"unknown component '{name}'")

    def is_global(self, name):
        if name in self.components:
            return self.components[name] is not bytes
        else:
            raise RuntimeError(f"unknown component '{name}'")