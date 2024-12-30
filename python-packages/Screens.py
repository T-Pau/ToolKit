"""
  Screens -- convert text screens
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

import os.path
import re
import sys

import enum


import AssemblerOutput
import RunlengthEncoder

class PageMode(enum.Enum):
    SINGLE = "single"
    OBJECTS = "objects"
    PAGES = "pages"

map_chars = r"'(.)'(?:-'(.)')?"
map_codes = r"\$([0-9a-fA-F]*)(?:-\$([0-9a-fA-F]*))?"

class ExpressionParser:
    def __init__(self, defines):
        self.tokens = []
        self.defines = defines

    def parse(self, tokens):
        self.tokens = tokens
        self.tokens.reverse()

        if len(self.tokens) == 0:
            raise RuntimeError("empty conditional")

        value = self.parse_expression()
        token = self.get()
        if token != "":
            raise RuntimeError(f"unexpected {token}")
        return value

    def get(self):
        if len(self.tokens) > 0:
            return self.tokens.pop()
        else:
            return ""

    def parse_expression(self):
        value = self.parse_term()
        token = self.get()
        if token == "and":
            return self.parse_expression() and value
        elif token == "or":
            return self.parse_expression() or value
        else:
            self.unget(token)
            return value

    def parse_term(self):
        token = self.get()
        if token == "not":
            return not self.parse_term()
        elif token == "(":
            value = self.parse_expression()
            if self.get() != ")":
                RuntimeError("syntax error, expected )")
            return value
        elif token == ")" or token == "and" or token == "or":
            raise RuntimeError(f"syntax error, unexpected {token}")
        else:
            return token in self.defines

    def unget(self, token):
        self.tokens.append(token)


class Source:
    def __init__(self, filename):
        self.filename = filename
        self.line_number = 0
        self.file = open(filename, mode="r")

    def readline(self):
        self.line_number += 1
        return self.file.readline()

    def error_prefix(self):
        return f"{self.filename}:{self.line_number}"


class Screens:
    def __init__(self, dependencies, options=None, defines=None, include_directories=None, images=None, assembler_output=None):
        self.name = ""
        self.title_length = 0
        self.title_xor = 0
        self.line_length = 40
        self.lines = 25
        self.line_skip = 0
        self.page_mode = PageMode.PAGES
        self.prefix = b""
        self.postfix = b""
        self.word_wrap = False
        self.include_directories = include_directories or []
        self.images = images or []
        self.image_padding_left = b""
        self.image_padding_right = b""

        self.dependencies = dependencies
        self.encoder = RunlengthEncoder.RunlengthEncoder()
        self.in_preamble = True
        self.compressed_screens = []
        self.screen_names = []
        self.current_line = 0
        self.current_title = b""
        self.current_name = None
        self.ignore_empty_line = False
        self.showing = [True]
        self.files = []
        self.input_file = ""
        self.ok = True
        self.assembler_output = assembler_output

        if options is not None:
            self.set_options(options)
        self.defines = {}
        self.charmap = {}

        if defines is not None:
            for define in defines:
                self.add_define(define)

    def add_define(self, define):
        parts = define.split("=")
        if len(parts) == 1:
            self.defines[define] = True
        else:
            self.defines[parts[0]] = parts[1]


    def convert(self, input_file, output_file):
        self.input_file = input_file
        self.dependencies.add(self.input_file)
        self.files = [Source(input_file)]
        self.in_preamble = True
        self.compressed_screens = []
        self.current_line = 0
        self.current_title = b""
        self.ignore_empty_line = False
        self.showing_else = [False]
        self.showing = [True]
        self.ok = True

        self.process()

        if not self.ok:
            return False

        self.write_output(output_file)
        return True

    def error(self, message):
        print(self.files[-1].error_prefix() + ": " + message, file=sys.stderr)
        self.ok = False

    def eval_if(self, expression):
        parser = ExpressionParser(self.defines)
        try:
            return parser.parse(expression)
        except Exception as e:
            self.error("invalid conditional: " + str(e))
            return False

    def find_file(self, file_name):
        if os.path.exists(file_name):
            return file_name
        for directory in [os.path.dirname(self.input_file)] + self.include_directories:
            name = os.path.join(directory, file_name)
            if os.path.exists(name):
                return name
        raise RuntimeError(f"file {file_name} not found")
    
    def process(self):
        while len(self.files) > 0:
            while line := self.files[-1].readline():
                self.process_line(line)
            if len(self.showing) != 1:
                self.error(f"unclosed .if")
            self.files.pop()
        self.end()

    def process_line(self, line):
        line = line.rstrip(" \n")
        if line.startswith("."):
            self.process_directive(line)
            return

        if not all(self.showing):
            return

        if line == "---":
            if self.in_preamble:
                self.in_preamble = False
            else:
                self.end_screen()
        else:
            if self.in_preamble:
                self.process_preamble_line(line)
            else:
                self.process_screen_line(line)

    def process_directive(self, line):
        line2 = line
        # TODO: strip ;.*
        line2.replace("(", " ( ")
        line2.replace(")", " ) ")
        words = line2.split()
        if words[0] == ".if":
            self.showing.append(self.eval_if(words[1:]))
            self.showing_else.append(not self.showing[-1])
            return
        elif words[0] == ".else":
            if len(self.showing) == 1:
                self.error(".else outside .if")
                return
            if len(words) > 1 and words[1] == "if":
                self.showing[-1] = self.eval_if(words[2:])
                self.showing_else[-1] = self.showing_else[-1] and not self.showing[-1]
            else:
                if len(words) > 1:
                    self.error("unexpected tokens after .else")
                self.showing[-1] = self.showing_else[-1]
            return
        elif line.startswith(".end"):
            if len(words) != 1:
                self.error("unexpected tokens after .else")
            if len(self.showing) == 1:
                self.error(".end outside .if")
                return
            self.showing.pop(-1)
            self.showing_else.pop(-1)
            return

        if not all(self.showing):
            return

        if line == ".image":
            if len(self.images) != 1:
                raise RuntimeError(".image without parameter but not exactly one image defined")
            self.add_image(self.images[0])
        elif line.startswith(".image "):
            index = int(line[7:])
            self.add_image(self.image[index])
        elif line.startswith(".include "):
            start = line.find("\"")
            end = line.rfind("\"")
            if start == end:
                raise RuntimeError("invalid .include")
            filename = self.find_file(line[start + 1:end])
            self.dependencies.add(filename)
            if filename.endswith(".bin"):
                self.include_binary_file(filename)
            else:
                self.files.append(Source(filename))
        elif line.startswith(".define "):
            self.add_define(line[8:])
        elif line.startswith(".skip "):
            self.encoder.skip(int(line.split(" ")[1]))
        else:
            self.error(f"invalid dot directive '{line}'")

    def include_binary_file(self, filename: str):
        with open(filename, "rb") as file:
            data = file.read()
            # TODO: handle prefix / postfix
            self.current_line += len(data) / self.line_length
            if self.current_line > self.lines:
                self.error("too many lines")
            self.encoder.add_bytes(data)

    def process_preamble_line(self, line):
        if line.startswith(";") or line == "":
            return
        elif line.startswith("prefix"):
            self.prefix = self.parse_fix(line)
        elif line.startswith("postfix"):
            self.postfix = self.parse_fix(line)
        else:
            words = line.split(" ")
            if words[0] == "image_padding_left":
                self.image_padding_left = self.map_string(words[1])
            elif words[0] == "image_padding_right":
                self.image_padding_right = self.map_string(words[1])
            elif words[0] == "line_length":
                self.line_length = int(words[1])
            elif words[0] == "line_skip":
                self.line_skip = int(words[1])
            elif words[0] == "lines":
                self.lines = int(words[1])
            elif words[0] == "map":
                self.add_map(words[1], words[2])
            elif words[0] == "name":
                self.name = words[1]
            elif words[0] == "page_mode":
                self.page_mode = PageMode(words[1])
            elif words[0] == "title_length":
                self.title_length = int(words[1])
            elif words[0] == "title_xor":
                self.title_xor = int(words[1])
            elif words[0] == "word_wrap":
                self.word_wrap = int(words[1])
            else:
                self.error(f"unknown command '{words[0]}'")

    def process_screen_line(self, line):
        if line == "---":
            self.end_screen()
        else:
            line = re.sub(r"\${[A-Z_]*}", lambda m: self.replace_variable(m), line)
            if self.title_length > 0 and self.current_title == b"":
                if len(line) > self.title_length:
                    self.error(f"title too long: '{line}'")
                self.add_string(line, self.title_length, self.title_xor)
                self.current_title = self.encoder.end()
                self.ignore_empty_line = True
                return
            elif self.page_mode == PageMode.OBJECTS and self.current_name is None:
                self.current_name = line
                self.ignore_empty_line = True
                return
            if self.ignore_empty_line and line == "":
                self.ignore_empty_line = False
                return
            self.ignore_empty_line = False
            if len(line) > self.line_length:
                if self.word_wrap:
                    short_line = ""
                    for word in line.split():
                        if len(short_line) + len(word) + 1 > self.line_length:
                            if len(short_line) > 0:
                                self.add_line(short_line)
                            else:
                                self.error(f"word too long: '{word}'")
                            short_line = word
                        else:
                            if len(short_line) > 0:
                                short_line += " "
                            short_line += word
                    self.add_line(short_line)
                    return
                else:
                    self.error(f"line too long: '{line}'")
            self.add_line(line)

    def add_line(self, line):
        self.current_line += 1
        if self.current_line == self.lines + 1:
            self.error(f"too many lines in screen")
        if self.current_line > 1 and self.line_skip > 0:
            self.encoder.skip(self.line_skip)
        self.encoder.add_bytes(self.prefix)
        self.add_string(line, self.line_length)
        self.encoder.add_bytes(self.postfix)

    def end_screen(self):
        if self.current_title != b"" or self.current_line > 0:
            while self.current_line < self.lines:
                self.add_line("")
            self.compressed_screens.append(self.current_title + self.encoder.end())
            self.current_title = b""
            self.current_line = 0
            if self.page_mode == PageMode.OBJECTS:
                self.screen_names.append(self.current_name)
            self.ignore_empty_line = False
            self.current_name = None

    def end(self):
        self.end_screen()

    def add_map(self, source_string, target_string):
        match = re.search(map_chars, source_string)
        if match:
            source_range = [ord(match.group(1)[0])]
            end = match.group(2)
            if end is not None:
                source_range.append(ord(end[0]))
        else:
            match = re.search(map_codes, source_string)
            if match:
                source_range = [int("0x" + match.group(1), 0)]
                end = match.group(2)
                if end is not None:
                    source_range.append(int("0x" + end, 0))
            else:
                raise RuntimeError(f"invalid map source {source_string}")
        if len(source_range) == 1:
            source_range.append(source_range[0])
        target = int(target_string.replace("$", "0x"), 0)

        for source in range(source_range[0], source_range[1] + 1):
            self.charmap[source] = target
            target += 1

    def add_bytes(self, string):
        self.encoder.add_bytes(string)

    def add_string(self, string, length, byte_xor=0):
        self.encoder.add_bytes(self.map_string(string.ljust(length), byte_xor))

    def map_string(self, string, byte_xor=0):
        result = b""
        for c in string:
            if ord(c) not in self.charmap:
                self.error(f"unmapped character '{c}'")
                continue
            result += (self.charmap[ord(c)] ^ byte_xor).to_bytes(1, byteorder="little")
        return result

    def parse_fix(self, line):
        # TODO: support for byte list
        start = line.find("\"")
        end = line.rfind("\"")
        return self.map_string(line[start + 1:end])

    def replace_variable(self, match):
        if match.group() is not None:
            name = match.group()[2:-1]
            if name not in self.defines:
                self.error(f"undefined variable '{name}'")
                return ""
            return self.defines[name]

    def set_options(self, options):
        for option, value in options:
            if option == "line_length":
                self.line_length = value
            elif option == "lines":
                self.lines = value
            elif option == "name":
                self.name = value
            elif option == "prefix":
                self.prefix = value
            elif option == "postfix":
                self.postfix = value
            elif option == "page_mode":
                self.page_mode = PageMode(value)
            elif option == "title_length":
                self.title_length = value
            elif option == "title_xor":
                self.title_xor = value

    def write_output(self, output_file):
        if self.assembler_output is not None:
            output = self.assembler_output
        else:
            output = AssemblerOutput.AssemblerOutput(output_file)
            output.header(self.input_file)
            output.section("data")
        if self.page_mode == PageMode.SINGLE:
            output.bytes_object(self.name, self.compressed_screens[0])
        elif self.page_mode == PageMode.OBJECTS:
            output.parts(self.name, self.compressed_screens, include_count=False, include_index=False, names=self.screen_names)
        else:
            output.parts(self.name, self.compressed_screens)

    def add_image(self, image):
        width = image["width"]
        height = image["height"]
        self.current_line += height
        if self.current_line > self.lines:
            self.error("too many lines")
        if len(self.image_padding_left) + len(self.image_padding_right) + width != self.line_length:
            self.error(f"image width {width} plus padding {len(self.image_padding_left)}+{len(self.image_padding_right)} is not line length {self.line_length}")
        # TODO: check that image width + padding is line length
        for y in range(height):
            self.add_bytes(self.image_padding_left)
            self.add_bytes(image["data"][width*y:width*(y+1)])
            self.add_bytes(self.image_padding_right)
