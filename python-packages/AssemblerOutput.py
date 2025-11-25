# AssemblerOutput -- create output in Accelerate assembler format
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

"""This module creates assembler source files in [Accelerate](https://accelerate.tpau.group/) format.
"""

import sys
from typing import IO, Any

class AssemblerOutput:
    """Create output files in Accelerate assembler format."""

    def __init__(self, file: IO[Any]) -> None:
        """Initialize assembler output.
        
        Args:
            file: The output file handle.
        """

        self.file = file
        self.current_section = None
        self.current_visibility = "private"

    def begin_object(self, name: str, section: str | None = None, visibility: str | None = None, alignment: int | None = None) -> None:
        """Begin a new object.
        
        Args:
            name: The name of the object.
            section: The section to place the object in. If `None`, place in current section.
            visibility: The visibility of the object.
            alignment: The alignment of the object.
        """

        if section is not None:
            self.section(section)
        self.empty_line()
        alignment_string = ""
        visibility_string = ""
        if visibility is not None and visibility != self.current_visibility:
            visibility_string = f".{visibility} "
        if alignment is not None:
            alignment_string = f" .align ${hex(alignment)[2:]}"
        print(f"{visibility_string}{name}{alignment_string} {{", file=self.file)

    def byte(self, value: Any) -> None:
        """Add a byte value as `.data` to current object.
        
        Args:
            value: The byte value.
        """
        print(f"    .data {value}", file=self.file)

    def bytes(self, bytes_array) -> None:
        """Add a byte array as `.data` to current object.

        Args:
            bytes_array: The byte array.
        """

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

    def bytes_object(self, name: str, bytes_array, section: str = "data", visibility: str | None = None, alignment: int | None = None) -> None:
        """Create an object containing a byte array.
        
        Args:
            name: The name of the object.
            bytes_array: The byte array.
            section: The section to place the object in. If `None`, place in current section.
            visibility: The visibility of the object.
            alignment: The alignment of the object.
        """

        self.begin_object(name, section=section, alignment=alignment, visibility=visibility)
        self.bytes(bytes_array)
        self.end_object()

    def combine_names(self, prefix: str | None, name: str | None) -> str:
        """Combine a prefix and name (either of which can be None) into a single name.
        
        Args:
            prefix: The prefix.
            name: The name.
            
        Returns:
            The combined name.

        Raises:
            RuntimeError: If both prefix and name are None.
        """

        if name is None:
            if prefix is None:
                raise RuntimeError("neither name nor prefix specified")
            return prefix
        elif prefix is None:
            return name
        else:
            return f"{prefix}_{name}"

    def comment(self, comment: str) -> None:
        """Add a comment line.

        Args:
            comment: The comment text.
        """

        print(f"; {comment}", file=self.file)

    def constant(self, name: str, value: Any) -> None:
        """Define a constant.

        Args:
            name: The name of the constant.
            value: The value of the constant.
        """

        print(f"{name} = {value}", file=self.file)

    def data_object(self, name: str, data: Any, section: str = "data", visibility: str | None = None, alignment: int | None = None) -> None:
        """Create an object containing data.

        Args:
            name: The name of the object.
            data: The data.
            section: The section to place the object in.
            visibility: The visibility of the object.
            alignment: The alignment of the object.
        """

        self.begin_object(name, section=section, alignment=alignment, visibility=visibility)
        self.data(data)
        self.end_object()

    def data(self, value: Any, encoding: str | None = None, line_length: int = 16) -> None:
        """Add data as `.data` to current object.

        Args:
            value: The data value or list of values.
            encoding: The encoding to use for strings.
            line_length: The number of values per line.
        """

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

    def empty_line(self) -> None:
        """Add an empty line to the output."""

        print("", file=self.file)

    def end_object(self) -> None:
        """End the current object."""

        print("}", file=self.file)

    def header(self, input_file: str | None) -> None:
        """Add standard file header comment.

        Args:
            input_file: The input file name, if any.
        """

        comment = f"This file is automatically created by {sys.argv[0]}"
        if input_file is not None:
            comment += f" from {input_file}"
        comment += "."
        self.comment(comment)
        self.comment(f"Do not edit.")
        self.empty_line()

    def label(self, name: str, visibility: str | None = None) -> None:
        """Add a label.

        Args:
            name: The name of the label.
            visibility: The visibility of the label.
        """

        visibility_string = ""
        if visibility is not None:
            visibility_string = f".{visibility} "
        print(f"{visibility_string}{name}:", file=self.file)

    def parts(self, name: str, parts: list, include_count: bool = True, include_index: bool = True, names: list | None = None) -> None:
        """Create multiple objects from parts.

        Args:
            name: The base name of the objects.
            parts: The data for each part.
            include_count: Whether to create an object with the count of parts.
            include_index: Whether to create an index object referencing each part.
            names: Optional list of name suffixes for the parts. If not provided, parts are named by their index.
        """

        if include_index:
            if include_count:
                self.begin_object(f"{name}_count")
                self.byte(len(parts))
                self.end_object()
            self.begin_object(name)
            for i in range(len(parts)):
                self.word(f"{name}_{i}")
            self.end_object()
        for i in range(len(parts)):
            self.begin_object(self.combine_names(name, names[i] if names else f"{i}"))
            self.bytes(parts[i])
            self.end_object()

    def pre_else(self) -> None:
        """Add a preprocessor else directive."""

        print(f".pre_else", file=self.file)

    def pre_end(self) -> None:
        """Add a preprocessor end directive."""
        print(f".pre_end", file=self.file)

    def pre_if(self, predicate: str) -> None:
        """Add a preprocessor if directive.

        Args:
            predicate: The predicate for the if directive.
        """
        print(f".pre_if {predicate}", file=self.file)

    def string(self, value: str, encoding: str | None = None, nul_terminate: bool = False) -> None:
        """Add a string as `.data` to current object.

        Args:
            value: The string value.
            encoding: The encoding to use for the string.
            nul_terminate: Whether to add a NUL terminator.
        """

        print(f"    .data \"{value}\"", end="", file=self.file)
        if encoding is not None:
            print(f":{encoding}", end="", file=self.file)
        if nul_terminate:
            print(", 0", end="", file=self.file)
        print("", file=self.file)

    def section(self, section: str) -> None:
        """Change current section.

        Args:
            section: The section name.
        """

        if self.current_section != section:
            self.empty_line()
            print(f".section {section}", file=self.file)
            self.current_section = section

    def visibility(self, visibility: str) -> None:
        """Change current visibility.

        Args:
            visibility: The visibility level.
        """

        if self.current_visibility != visibility:
            self.empty_line()
            print(f".visibility {visibility}", file=self.file)
            self.current_visibility = visibility

    def word(self, value: Any) -> None:
        """Add a word value as `.data` to current object.

        Args:
            value: The word value.
        """

        print(f"    .data {value}:2", file=self.file)
