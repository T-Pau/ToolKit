"""
  BASICOutput -- create BASIC program
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

import re
import sys

label_pattern = re.compile(r"^{{([^}]*)}}:$")
reference_pattern = re.compile(r"{{([^}]*)}}")


class BASICOutput:
    def __init__(self, file):
        self.file = file
        self.lines = []
        self.labels = {}
        self.subroutines = {}

    def add_line(self, line):
        match = label_pattern.match(line)
        if match:
            self.add_label(match.group(1))
        else:
            self.lines.append(line)
    
    def add_lines(self, lines):
        for line in lines:
            self.add_line(line)
    
    def add_label(self, label):
        if label in self.labels:
            raise RuntimeError(f"duplicate definition of label {label}")
        if label in self.subroutines:
            raise RuntimeError(f"label {label} conflicts with subroutine of same name")
        self.labels[label] = len(self.lines)
    
    def add_subroutine(self, name, lines):
        if name in self.subroutines:
            raise RuntimeError(f"duplicate definition of subroutine {name}")
        if name in self.labels:
            raise RuntimeError(f"subroutine {label} conflicts with label of same name")
        self.subroutines[name] = lines

    def add_subroutines(self, subroutines):
        for name, subroutine in subroutines.items():
            self.add_subroutine(name, subroutine)

    def end(self):
        self.resolve_subroutines()
        for number, text in enumerate(self.lines):
            while match := reference_pattern.search(text):
                name = match.group(1)
                if name not in self.labels:
                    raise RuntimeError(f"undefined label {name}")
                text = text[:match.start()] + f"{self.labels[name]}" + text[match.end():]
            print(f"{number} {text}", file=self.file)

    def resolve_subroutines(self):
        for line in self.lines:
            for match in re.finditer(reference_pattern, line):
                name = match.group(1)
                if name in self.subroutines:
                    lines = self.subroutines[name]
                    del self.subroutines[name]
                    self.add_label(name)
                    self.add_lines(lines)
