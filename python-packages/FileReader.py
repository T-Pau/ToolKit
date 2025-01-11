import os.path
import sys

"""
  FileReader -- read file line by line with error reporting and preprocessor
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

class FileReader:
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
        
    def __init__(self, script, filename, preprocess=False, defines={}):
        self.script = script
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

    def get_line(self):
        while len(self.sources) > 0:
            line = self.current_source().get_line()
            if line is not None:
                return line
            self.sources.pop()
        return None

    def fail(self):
        self.ok = False

    def message(self, message):
        if len(self.sources) > 0:
            print(self.current_source().message_prefix(), file=sys.stderr, end="")
        print(message, file=sys.stderr)

    def error(self, message):
        self.message("error: " + message)
        self.fail()
    
    def warning(self, message):
        self.message("warning: " + message)

    # Internal Methods

    def current_source(self):
        if len(self.sources) > 0:
            return self.sources[-1]
        else:
            return None
