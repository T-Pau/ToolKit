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
