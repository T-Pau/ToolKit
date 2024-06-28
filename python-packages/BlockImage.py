"""
  BlockImage -- convert image to blocks with color restrictions
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

class BitStream:
    def __init__(self) -> None:
        self.data = b""
        self.partial = 0
        self.partial_bits = 0
    
    def reset(self):
        self.data = b""
        self.partial = 0
        self.partial_bits = 0

    def add(self, value, bits):
        self.partial <<= bits
        self.partial |= value
        self.partial_bits += bits

        if self.partial_bits >= 8:
            rest_bits = self.partial_bits % 8
            encode_bytes = self.partial_bits // 8
            self.data += (self.partial >> rest_bits).to_bytes(encode_bytes, byteorder="big")
            self.partial &= 0xff >> (8 - rest_bits)
            self.partial_bits = rest_bits
        

class BlockImage:
    class Block:
        def __init__(self, width, height) -> None:
            self.colors = {}
            self.pixels = [[None for x in range(width)] for y in range(height)]
            self.width = width
            self.height = height
        
        def set(self, x, y, color):
            self.pixels[y][x] = color
            self.colors[color] = 1
        
        def num_colors(self):
            return len(self.colors)
        
        def get_colors(self):
            return sorted(self.colors.keys())

        def encode(self, colors, bits=None):
            if bits is None:
                bits = (len(colors) - 1).bit_length()
            elif bits < (len(colors) - 1).bit_length():
                raise RuntimeError("not enough bits to encode colors")
            if (self.width * bits) % 8 != 0:
                raise RuntimeError("can't encode block with partial byte width")
            
            color_map = {}
            for i, c in enumerate(colors):
                color_map[c] = i
            
            rows = []
            for y in range(self.height):
                bitstream = BitStream()
                for x in range(self.width):
                    c = self.pixels[y][x]
                    if c not in color_map:
                        raise RuntimeError(f"invalid color {c}")
                    bitstream.add(color_map[c], bits)
                rows.append(bitstream.data)

            return rows


    def __init__(self, filename, block_width, block_height, palette, pixel_size=PaletteImage.PixelSize(1, 1)):
        self.image = PaletteImage.PaletteImage(filename, palette, pixel_size)
        self.block_width = block_width
        self.block_height = block_height
        if self.image.width % self.block_width != 0:
            raise RuntimeError(f"image width not multiple of block width")
        if self.image.height % self.block_height != 0:
            raise RuntimeError(f"image height not multiple of block height")
        self.width = self.image.width // self.block_width
        self.height = self.image.height // self.block_height

    def get(self, x, y):
        x *= self.block_width
        y *= self.block_height
        block = BlockImage.Block(self.block_width, self.block_height)

        for yy in range(self.block_height):
            for xx in range(self.block_width):
                block.set(xx, yy, self.image.get(x + xx, y + yy))

        return block

    def get_blocks(self):
        return [[self.get(x, y) for x in range(self.width)] for y in range(self.height)]
