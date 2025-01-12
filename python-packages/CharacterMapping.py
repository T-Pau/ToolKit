"""
  CharacterMapping -- Map Unicode characters to native encoding.
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

pattern_hex = r"(?:0x|$)([0-9a-fA-F]+)(.*)"
pattern_dec = r"([0-9]+)(.*)"

class CharacterMapping:
    @staticmethod
    def petscii():
        return CharacterMapping([
            [" ", "[", 0x20],
            ["£", 0x5c],
            ["]", 0x5d],
            # TODO: arrows up and left
            ["a", "z", 0x41],
            ["┃", 0x62],
            ["─", 0x63],
            ["━", 0x63],
            ["╮", 0x69],
            ["╲", 0x6d],
            ["╱", 0x6e],
            ["╳", 0x76],
            ["╋", 0x7b],
            ["▔", 0xa3],
            ["┣", 0xab],
            ["┗", 0xad],
            ["┓", 0xae],
            ["┏", 0xb0],
            ["┻", 0xb1],
            ["┳", 0xb2],
            ["┫", 0xb3],
            ["┛", 0xbd]
        ])

    def __init__(self, mappings=[]):
        self.charmap = {}
        for mapping in mappings:
            self.add_mapping(mapping)
    
    def add_mapping(self, arguments):
        if type(arguments) is list:
            if len(arguments) == 2:
                self.add_single(arguments[0], arguments[1])
            elif len(arguments) == 3:
                self.add_range(arguments[0], arguments[1], arguments[2])
            else:
                raise RuntimeError("invalid mapping with {len(arguments)} elements")
        else:
            (source_start, arguments) = self.parse_source(arguments)
            if arguments == "":
                raise RuntimeError("incomplete map specification")
            if arguments[0] == '-':
                (source_end, arguments) = self.parse_source(arguments[1:])
                if arguments == "":
                    raise RuntimeError("incomplete map specification")
            else:
                source_end = source_start
            if arguments[0] != ':':
                raise RuntimeError("expected ':' in map specification")
            (target, arguments) = self.parse_target(arguments[1:])
            if arguments != "":
                raise RuntimeError("trailing garbage in map specification")
            self.add_range(source_start, source_end, target)

    def add_range(self, source_start, source_end, target):
        if type(source_start) == str:
            source_start = ord(source_start)
        if type(source_end) == str:
            source_end = ord(source_end)
        for source in range(source_start, source_end + 1):
            self.charmap[chr(source)] = target.to_bytes(1, "little")
            target += 1

    def add_single(self, character, target):
        if type(character) == int:
            character = chr(character)
        self.charmap[character] = target.to_bytes(1, "little")

    def encode(self, string):
        result = b""
        for character in string:
            if character not in self.charmap:
                raise RuntimeError(f"unmapped character '{character}'")
            result += self.charmap[character]
        return result

    # Private methods

    def parse_source(self, arguments):
        arguments.strip()
        if arguments[0] == "'" or arguments[0 == '"']:
            if arguments[3] != arguments[0]:
                raise RuntimeError("character map source longer than one character")
            return (arguments[2], arguments[3:].strip())
        else:
            return self.parse_int(arguments, 0xffff)

    def parse_target(self, arguments):
        return self.parse_int(arguments, 0xff)

    def parse_int(self, arguments, max_value):
            if match := re.match(pattern_hex, arguments):
                value = int("0x" + match.group(1))
                arguments = match.group(2)
            elif match := re.match(pattern_dec, arguments):
                value = int(match.group(1))
                arguments = match.group(2)
            else:
                raise RuntimeError("invalid mapping value")
            if value > max_value:
                raise RuntimeError("mapping value too large")
            return (value, arguments.strip())
