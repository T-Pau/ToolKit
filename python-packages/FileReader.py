import os.path
import sys

# FileReader -- read file line by line with error reporting and preprocessor
# Copyright (C) Dieter Baron
#
# The author can be contacted at <dillo@tpau.group>.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. The names of the authors may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
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

import os
import traceback

class FileReader:
    """Read file line by line with error reporting and preprocessor."""
    class Source:
        def __init__(self, filename):
            self.filename = filename
            self.file = open(self.filename, "r")
            self.line_number = 0
        
        def get_line(self):
            if self.file is None:
                return None
            self.line_number += 1
            line = self.file.readline()
            if not line:
                self.file = None
                return None
            return line

        def message_prefix(self):
            return f"{self.filename}:{self.line_number}: "
        
    def __init__(self, filename: str, preprocess: bool = False, defines: dict = {}):
        """Initialize FileReader.
        
        Arguments:
            filename: file to read
            preprocess: whether to run preprocessor
            defines: dictionary with preprocessor defines
        """
        self.preprocess = preprocess
        self.defines = defines
        self.sources = [FileReader.Source(filename)]
        self.ok = True

    def __iter__(self):
        return self
    
    def __next__(self):
        line = self.get_line()
        if line is None:
            raise StopIteration
        return line

    def get_line(self) -> str | None:
        """Get next line from file, or None if at end of file.
        
        Returns:
            next line from file, or None if at end of file"""

        while True:
            source = self._current_source()
            if source is None:
                return None
            line = source.get_line()
            if line is not None:
                return line
            self.sources.pop()

    def fail(self):
        """Mark reader as failed."""

        self.ok = False

    def message(self, message: str):
        """Print message to standard error, prefixed with current file position.

        Arguments:
            message: message to print
        """

        source = self._current_source()
        if source is not None:
            print(source.message_prefix(), file=sys.stderr, end="")
        print(message, file=sys.stderr)

    def error(self, message: str | BaseException):
        """Print error message and mark reader as failed.

        Arguments:
            message: error message or exception to print
        """

        if isinstance(message, BaseException):
            if "TOOLKIT_DEBUG" in os.environ:
                traceback.print_exception(message)
            message = str(message)
        self.message("error: " + message)
        self.fail()
    
    def warning(self, message: str):
        """Print warning message.

        Arguments:
            message: warning message to print
        """

        self.message("warning: " + message)

    def _current_source(self) -> "FileReader.Source | None":
        """Get current source.
        
        Returns:
            current source, or None if there is none"""

        if len(self.sources) > 0:
            return self.sources[-1]
        else:
            return None
