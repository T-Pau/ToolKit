import os.path
import sys

"""
  Dependencies -- create gcc style dependencies file
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

class Dependencies:
    def __init__(self, filename: str, target: str) -> None:
        self.dependencies = set()
        self.filename = filename
        self.target = target
        self.dependencies.add(sys.argv[0])
        directory = os.path.dirname(__file__)
        for module in sys.modules.keys():
            filename = os.path.join(directory, f"{module}.py")
            if os.path.exists(filename):
                self.dependencies.add(filename)

    def add(self, filename: str) -> None:
        self.dependencies.add(filename)

    def write(self) -> None:
        if self.filename is not None:
            with open(self.filename, "w") as file:
                print(f"{self.target}: ", end="", file=file)
                print(" ".join(self.dependencies), file=file)

    def check(self) -> None:
        if not os.path.exists(self.target):
            raise RuntimeError(f"failed to create output file '{self.target}'")
        target_mtime = os.path.getmtime(self.target)
        depends_mtime = None
        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise RuntimeError(f"failed to create dependency file '{self.filename}'")
            depends_mtime = os.path.getmtime(self.filename)

        for dependency in self.dependencies:
            if not os.path.exists(dependency):
                raise RuntimeError(f"dependency '{dependency}' does not exist")
            mtime = os.path.getmtime(dependency)
            if mtime > target_mtime:
                raise RuntimeError(f"dependency '{dependency}' is newer than output file '{self.target}'")
            if depends_mtime is not None and mtime > depends_mtime:
                raise RuntimeError(f"dependency '{dependency}' is newer than dependency file '{self.filename}'")
