# AtomicOutput.py -- create output only if no errors occurred
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
This module creates the output file only if no errors occurred.
"""

import os
import sys
import traceback
from typing import Any, Callable, IO


class AtomicOutput:
    """Create output file only if no errors occurred."""

    def __init__(self):
        self.binary = False
        self.filename = None
        self.only_if_changed = False
        self.temp_name = None
        self.file = None
        self.ok = True

    def set_filename(self, filename: str, binary: bool = False):
        """Set output filename.
        
        Args:
            filename: The output filename.
            binary: Whether to open the file in binary mode.
        
        Raises:
            RuntimeError: If the output file is already open.
        """

        if self.file is not None:
            raise RuntimeError("can't change output filename after opening file")
        self.binary = binary
        self.filename = filename

    def set_only_if_changed(self, value: bool):
        """Set whether not to overwrite an existing file if it remains unchanged. This avoids unnecessary rebuilds.

        Raises:
            RuntimeError: If the output file is already open.
        """
        if self.file is not None:
            raise RuntimeError("can't change only-if-changed after opening file")
        self.only_if_changed = value

    def get_filename(self) -> str:
        """Get the output filename.
        
        Returns:
            The output filename.

        Raises:
            RuntimeError: If the output filename is not set.
        """

        if self.filename is None:
            raise RuntimeError("output filename not set")
        if self.temp_name is None:
            if self.only_if_changed:
                self.temp_name = self.filename + "XXX"  # TODO: make unique name with pid
            else:
                self.temp_name = self.filename
        return self.temp_name

    def get_file(self) -> IO[Any]:
        """Get the output file handle, opening the file if necessary.
        
        Returns:
            The output file handle.
        """

        if self.file is None:
            self.file = open(self.get_filename(), self.mode())
        return self.file

    def fail(self) -> None:
        """Mark the output as failed, discarding the output."""

        self.ok = False

    def abort(self, message: str) -> None:
        """Abort the operation with an error message and discard the output.
        
        Args:
            message: The error message.
        """

        print(f"{sys.argv[0]}: {message}", file=sys.stderr)
        self.discard()
        exit(1)

    def close(self) -> None:
        """Close the output file."""

        if self.file is not None:
            self.file.close()
            self.file = None
        # if self.temp_name is not None and self.only_if_changed: # TODO: move temp_name to filename

    def discard(self) -> None:
        """Discard the output file."""

        if self.file is not None:
            self.file.close()
            self.file = None
        if self.temp_name and os.path.exists(self.temp_name):
            os.remove(self.temp_name)

    def error(self, message: str) -> None:
        """Report an error and mark the output as failed.
        
        Args:
            message: The error message.
        """

        print(message, file=sys.stderr)
        self.fail()

    def run(self, code: Callable[[], None]) -> bool:
        """Run code that produces the output file. If an uncaught exception occurs, the output file is discarded.

        Args:
            code: The function to call to produce the output file.
        """

        try:
            code()
            if not self.ok:
                raise RuntimeError("")
            self.close()
            return True
        except Exception as ex:
            if "TOOLKIT_DEBUG" in os.environ:
                traceback.print_exception(ex)
            elif str(ex) != "":
                print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
            self.discard()
            return False

    # private methods

    def mode(self) -> str:
        if self.binary:
            return "wb"
        else:
            return "w"
