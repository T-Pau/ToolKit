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
    def __init__(self, colors):
        self.colors = {}
        self.max_index = 0
        self.add_colors(colors)

    def __contains__(self, color):
        return color in self.colors
    
    def __copy__(self):
        copy = Palette({})
        copy.colors = self.colors.copy()
        copy.max_index = self.max_index
        return copy
    
    def __getitem__(self, color):
        return self.colors[color]

    def __len__(self):
        return len(self.colors)

    def add_colors(self, colors):
        if colors is None:
            return
        
        for color, index in colors.items():
            self.colors[color] = index
            if index is not None and index > self.max_index:
                self.max_index = index
    
    def bit_length(self):
        return self.max_index.bit_length()

c64 = Palette({
    0x000000: 0, # black
    0xffffff: 1, # white 
    0x6D242B: 2, # red
    0x65C5BC: 3, # cyan
    0x7A2585: 4, # purple
    0x48A03C: 5, # green
    0x221989: 6, # blue
    0xE9F15E: 7, # yellow
    0x7A3E1F: 8, # orange
    0x432B01: 9, # brown
    0xB5565E: 10, # light-red
    0x393939: 11, # grey-1
    0x686868: 12, # grey-2
    0x9CFF8E: 13, # light-green
    0x5C52E6: 14, # light-blue
    0xA3A3A3: 15  # grey-3
})

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
})