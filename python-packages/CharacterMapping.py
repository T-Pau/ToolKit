# CharacterMapping -- Map Unicode characters to native encoding.
# Copyright (C) Dieter Baron
#
# The author can be contacted at <dillo@tpau.group>.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2. The names of the authors may not be used to endorse or promote
#     products derived from this software without specific prior
#     written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This module maps Unicode characters to native encoding.

Source characters can be specified as Unicode characters (`"<character>"` or `'<character>'`), as decimal values (`<number>`), or as hexadecimal values (`0x<number>`).

Destination characters are specified as integer values.

Mapping specifications can be given as a list or a string:

- A list specification has the following formats:

    - For single character mapping: `[<source>, <target>]`

    - For range mapping: `[<source_start>, <source_end>, <target_start>]`

- A string specification has the following format:

    - For single character mapping: `<source>:<target>`

    - For range mapping: `<source_start>-<source_end>:<target_start>`
"""

import re

pattern_hex = r"(?:0x|$)([0-9a-fA-F]+)(.*)"
pattern_dec = r"([0-9]+)(.*)"

class CharacterMapping:
    """Map Unicode characters to native encoding."""

    @staticmethod
    def petscii() -> "CharacterMapping":
        """Create PETSCII character mapping.

        Returns:
            PETSCII character mapping.
        """
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

    def __init__(self, mappings: list[list[int|str]|str] = []):
        """Initialize character mapping.

        Args:
            mappings: List of mappings to add.
        """

        self.charmap = {}
        for mapping in mappings:
            self.add_mapping(mapping)
    
    def add_mapping(self, arguments: list[int|str] | str) -> None:
        """Add a mapping.

        Args:
            arguments: Mapping to add.

        Raises:
            ValueError: If mapping specification is invalid.
        """

        if type(arguments) is list:
            if len(arguments) == 2:
                if type(arguments[1]) is not int:
                    raise ValueError("target must be an integer")
                self.add_single(arguments[0], arguments[1])
            elif len(arguments) == 3:
                if type(arguments[2]) is not int:
                    raise ValueError("target must be an integer")
                self.add_range(arguments[0], arguments[1], arguments[2])
            else:
                raise ValueError("invalid mapping with {len(arguments)} elements")
        elif type(arguments) is str:
            (source_start, arguments) = self._parse_source(arguments)
            if arguments == "":
                raise ValueError("incomplete map specification")
            if arguments[0] == '-':
                (source_end, arguments) = self._parse_source(arguments[1:])
                if arguments == "":
                    raise ValueError("incomplete map specification")
            else:
                source_end = source_start
            if arguments[0] != ':':
                raise ValueError("expected ':' in map specification")
            (target, arguments) = self._parse_target(arguments[1:])
            if arguments != "":
                raise ValueError("trailing garbage in map specification")
            self.add_range(source_start, source_end, target)
        else:
            raise ValueError(f"invalid mapping specification type {type(arguments)}")

    def add_range(self, source_start: int | str, source_end: int | str, target: int):
        """Add a range of mappings.

        Args:
            source_start: Start of Unicode character range.
            source_end: End of Unicode character range.
            target: Start of native character range.
        """

        if type(source_start) == str:
            source_start = ord(source_start)
        if type(source_end) == str:
            source_end = ord(source_end)
        for source in range(source_start, source_end + 1): # type: ignore
            self.charmap[chr(source)] = target.to_bytes(1, "little")
            target += 1

    def add_single(self, character: int | str, target: int):
        """Add a single mapping.

        Args:
            character: Unicode character.
            target: Native character.
        """

        if type(character) == int:
            character = chr(character)
        self.charmap[character] = target.to_bytes(1, "little")

    def encode(self, string: str) -> bytes:
        """Encode Unicode string.

        Args:
            string: String to encode.

        Returns:
            Encoded string.

        Raises:
            ValueError: If string contains unmapped characters.
        """

        result = b""
        for character in string:
            if character not in self.charmap:
                raise ValueError(f"unmapped character '{character}'")
            result += self.charmap[character]
        return result

    # Private methods

    def _parse_source(self, arguments: str) -> tuple[int | str, str]:
        """Parse source character from mapping specification.

        Args:
            arguments: Mapping specification.
        
        Returns:
            Tuple of parsed source character and remaining arguments.
        Raises:
            ValueError: If source character is invalid or too large.
        """
        arguments = arguments.strip()
        if arguments[0] == "'" or arguments[0] == '"':
            if arguments[3] != arguments[0]:
                raise ValueError("character map source longer than one character")
            return (arguments[2], arguments[3:].strip())
        else:
            return self._parse_int(arguments, 0xffff)

    def _parse_target(self, arguments: str) -> tuple[int, str]:
        """Parse target character from mapping specification.

        Args:
            arguments: Mapping specification.
        Returns:
            Tuple of parsed target character and remaining arguments.
        Raises:
            ValueError: If target character is invalid or too large.
        """
        return self._parse_int(arguments, 0xff)

    def _parse_int(self, arguments: str, max_value: int) -> tuple[int, str]:
        """Parse integer from mapping specification.

        Args:
            arguments: Mapping specification.
            max_value: Maximum allowed value.   
        
        Returns:
            Tuple of parsed integer and remaining arguments.
        Raises:
            ValueError: If integer is invalid or too large.
        """
        arguments = arguments.strip()
        if match := re.match(pattern_hex, arguments):
            value = int("0x" + match.group(1))
            arguments = match.group(2)
        elif match := re.match(pattern_dec, arguments):
            value = int(match.group(1))
            arguments = match.group(2)
        else:
            raise ValueError("invalid mapping value")
        if value > max_value:
            raise ValueError("mapping value too large")
        return (value, arguments.strip())
