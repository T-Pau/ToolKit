"""
  AssemblerOutput -- create output in various assembler formats
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


import sys


class AssemblerOutput:
    def __init__(self, file):
        self.file = file
        self.current_section = None
        self.current_visibility = "private"

    def begin_object(self, name, section=None, visibility=None, alignment=None):
        if section is not None:
            self.section(section)
        self.empty_line()
        alignment_string = ""
        visibility_string = ""
        if visibility is not None and visibility != self.current_visibility:
            visibility_string = f".{visibility} "
        if alignment is not None:
            alignment_string = f" .align {alignment}"
        print(f"{visibility_string}{name}{alignment_string} {{", file=self.file)

    def byte(self, value):
        print(f"    .data {value}", file=self.file)

    def bytes(self, bytes_array):
        i = 0
        for byte in bytes_array:
            if i == 0:
                self.file.write("    .data ")
            else:
                self.file.write(", ")
            self.file.write(f'${byte:02x}')
            i += 1
            if i == 8:
                self.file.write("\n")
                i = 0
        if i > 0:
            self.file.write("\n")

    def bytes_object(self, name, bytes_array, section="data", visibility=None, alignment=None):
        self.begin_object(name, section=section, alignment=alignment)
        self.bytes(bytes_array)
        self.end_object()

    def comment(self, comment):
        print(f"; {comment}", file=self.file)

    def data(self, value, encoding=None, line_length=16):
        if type(value) != list:
            value = [value]

        index = 0
        for v in value:
            if index % line_length == 0:
                if index > 0:
                    print(file=self.file)
                print(f"    .data ", end="", file=self.file)
            else:
                print(", ", end="", file=self.file)
            print(f"{v}", end="", file=self.file)
            if encoding is not None:
                print(f":{encoding}", file=self.file)
            index += 1
        print("", file=self.file)

    def empty_line(self):
        print("", file=self.file)

    def end_object(self):
        print("}", file=self.file)

    def header(self, input_file):
        self.comment(f"This file is automatically created by {sys.argv[0]} from {input_file}.")
        self.comment(f"Do not edit.")
        self.empty_line()

    def parts(self, name, parts, include_count=True):
        if include_count:
            self.begin_object(f"{name}_count")
            self.byte(len(parts))
            self.end_object()
        self.begin_object(name)
        for i in range(len(parts)):
            self.word(f"{name}_{i}")
        self.end_object()
        for i in range(len(parts)):
            self.begin_object(f"{name}_{i}")
            self.bytes(parts[i])
            self.end_object()

    def pre_else(self):
        print(f".pre_else", file=self.file)

    def pre_end(self):
        print(f".pre_end", file=self.file)

    def pre_if(self, predicate):
        print(f".pre_if {predicate}", file=self.file)

    def string(self, value, encoding=None):
        print(f"    .data \"{value}\"", end="", file=self.file)
        if encoding is not None:
            print(f":{encoding}", end="", file=self.file)
        print("", file=self.file)

    def section(self, section):
        if self.current_section != section:
            self.empty_line()
            print(f".section {section}", file=self.file)
            self.current_section = section

    def visibility(self, visibility):
        if self.current_visibility != visibility:
            self.empty_line()
            print(f".visibility {visibility}", file=self.file)
            self.current_visibility = visibility

    def word(self, value):
        print(f"    .data {value}:2", file=self.file)
