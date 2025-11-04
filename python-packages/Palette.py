"""
  Palette -- map colors to indices
  Copyright (C) Dieter Baron

  The authors can be contacted at <toolkit@tpau.group>.

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

class Palette:
    def __init__(self, colors: dict[int|str, int | None] | list[int|str], names: dict[str, int] | list[str] | None = None) -> None:
        self.colors = {}
        self.names = {}
        self.max_index = 0
        self.add_colors(colors)
        if names is not None:
            self.add_names(names)

    def __contains__(self, color: str | int | tuple[int, ...] | float | None) -> bool:
        if color is None:
            return True
        if isinstance(color, str):
            return color in self.names
        else:
            color = self.normalize_color(color)
            return color in self.colors

    def __copy__(self) -> "Palette":
        copy = Palette({})
        copy.colors = self.colors.copy()
        copy.max_index = self.max_index
        copy.names = self.names.copy()
        return copy

    def __getitem__(self, color: str | int | tuple[int, ...] | float | None) -> int | None:
        if color is None:
            return None
        if isinstance(color, str):
            if color not in self.names:
                raise KeyError(f"color name '{color}' not in palette")
            return self.names[color]
        else:
            color = self.normalize_color(color)
            if color not in self.colors:
                raise KeyError(f"color {color:#08x} not in palette")
            return self.colors[color]

    def __len__(self) -> int:
        return len(self.colors)

    def add_colors(self, colors: dict[int|str, int | None] | list[int|str]) -> None:
        if isinstance(colors, list):
            for color in colors:
                if self.max_index == 0 and len(self.colors) == 0:
                    index = 0
                else:
                    index = self.max_index + 1
                self.add_color(color, index)
        else:
            for value, index in colors.items():
                self.add_color(value, index)

    def add_color(self, color: int | str, index: int | None) -> None:
        if isinstance(color, str):
            if color in global_colors:
                color = global_colors[color]
            elif "." in color:
                palette, name = color.split(".", 1)
                colors = palettes[palette].get_colors(name)
                for color in colors:
                    self.add_color(color, index)
                return
            else:
                color = int(color, 16)

        color = self.normalize_color(color)

        if color in self.colors:
            raise RuntimeError(f"duplicate color {color:#08x} in palette")

        self.colors[color] = index
        if index is not None and index > self.max_index:
            self.max_index = index

    def add_names(self, names: dict[str, int] | list[str]) -> None:
        if isinstance(names, list):
            for name in names:
                self.add_name(name, len(self.names))
        else:
            for name, index in names.items():
                self.add_name(name, index)
        
    def add_name(self, name: str, index: int) -> None:
        if name in self.names:
            raise RuntimeError(f"duplicate name '{name}' in palette")
        if index < 0 or index > self.max_index:
            raise RuntimeError(f"invalid index {index} for name '{name}'")
        self.names[name] = index

    def normalize_color(self, color: int | tuple[int, ...] | float) -> int:
        if isinstance(color, tuple):
            if len(color) < 3:
                raise RuntimeError(f"invalid color tuple {color}")
            alpha = color[3] if len(color) > 3 else 255
            if alpha == 0:
                rgb_color = 0xff000000
            else:
                rgb_color = (255-alpha) << 24 | color[0] << 16 | color[1] << 8 | color[2]
            color = rgb_color
        elif isinstance(color, float):
            raise RuntimeError("float colors not supported")
        return color

    def bit_length(self) -> int:
        return self.max_index.bit_length()

    # Return all color values matching the given index or name.
    def get_colors(self, color: str | int) -> list[int]:
        if isinstance(color, str):
            if color not in self.names:
                raise KeyError(f"color name '{color}' not in palette")
            index = self.names[color]
        else:
            if color < 0 or color > self.max_index:
                raise KeyError(f"invalid index {color}")
            index = color
        return [color for color, idx in self.colors.items() if idx == index]
    
    # Return index of given name.
    def get_index(self, name: str) -> int:
        if name not in self.names:
            raise KeyError(f"color name '{name}' not in palette")
        return self.names[name]

c64 = Palette([
    0x000000, #  0: black
    0xffffff, #  1: white
    0x6d242b, #  2: red
    0x65c5bc, #  3: cyan
    0x7a2585, #  4: purple
    0x48a03c, #  5: green
    0x221989, #  6: blue
    0xe9f15e, #  7: yellow
    0x7a3e1f, #  8: orange
    0x432b01, #  9: brown
    0xb5565e, # 10: light-red
    0x393939, # 11: grey-1
    0x686868, # 12: grey-2
    0x9cff8e, # 13: light-green
    0x5c52e6, # 14: light-blue
    0xa3a3a3  # 15: grey-3
], [
    "black",
    "white",
    "red",
    "cyan",
    "purple",
    "green",
    "blue",
    "yellow",
    "orange",
    "brown",
    "light-red",
    "grey-1",
    "grey-2",
    "light-green",
    "light-blue",
    "grey-3"
])

spectrum = Palette({
    0x000000: 0, # black
    0x0022c7: 1, # blue
    0xd62816: 2, # red
    0xd433c7: 3, # magenta
    0x00c525: 4, # green
    0x00c7c9: 5, # cyan
    0xccc82a: 6, # yellow
    0xcacaca: 7, # white
    0x002bfb: 9, # bright blue
    0xff331c: 10, # bright red
    0xff40fc: 11, # bright magenta
    0x00f92f: 12, # bright green
    0x00fbfe: 13, # bright cyan
    0xfffc36: 14, # bright yellow
    0xffffff: 15 # bright white
}, {
    "black": 0,
    "blue": 1,
    "red": 2,
    "magenta": 3,
    "green": 4,
    "cyan": 5,
    "yellow": 6,
    "white": 7,
    "bright-blue": 9,
    "bright-red": 10,
    "bright-magenta": 11,
    "bright-green": 12,
    "bright-cyan": 13,
    "bright-yellow": 14,
    "bright-white": 15
})

palettes = {
    "c64": c64,
    "spectrum": spectrum
}

global_colors = {
    "black": 0x000000,
    "grey-25": 0x404040,
    "grey-33": 0x555555,
    "grey-50": 0x808080,
    "grey-66": 0xaaaaaa,
    "grey-75": 0xc0c0c0,
    "white": 0xffffff,
    "transparent": 0xff000000
}
