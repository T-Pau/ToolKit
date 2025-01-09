"""
  AtomicOutput.py -- create output only if no errors occurred
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

import os
import sys
import traceback


class AtomicOutput:
    def __init__(self):
        self.binary = False
        self.filename = None
        self.only_if_changed = False
        self.temp_name = None
        self.file = None
        self.ok = True

    def set_filename(self, filename, binary=False):
        if self.file is not None:
            raise RuntimeError("can't change output filename after opening file")
        self.binary = binary
        self.filename = filename

    def set_only_if_changed(self, value):
        if self.file is not None:
            raise RuntimeError("can't change only-if-changed after opening file")
        self.only_if_changed = value

    def get_filename(self):
        if self.temp_name is None:
            if self.only_if_changed:
                self.temp_name = self.filename + "XXX"  # TODO: make unique name with pid
            else:
                self.temp_name = self.filename
        return self.temp_name

    def get_file(self):
        if self.file is None:
            self.file = open(self.get_filename(), self.mode())
        return self.file

    def abort(self, message):
        print(f"{sys.argv[0]}: {message}", file=sys.stderr)
        self.discard()
        exit(1)

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        # if self.temp_name is not None and self.only_if_changed: # TODO: move temp_name to filename

    def discard(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.temp_name and os.path.exists(self.temp_name):
            os.remove(self.temp_name)
    
    def error(self, message):
        print(message, file=sys.stderr)
        self.ok = False

    def run(self, code):
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

    def mode(self):
        if self.binary:
            return "wb"
        else:
            return "w"
