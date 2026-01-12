# Command -- run external command
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

import os
import shutil
import subprocess

class Command:
    """Run external command with arguments.
    
    Attributes:
        exit_code: exit code of the command after running it
        stdout: standard output of the command after running it
        stderr: standard error of the command after running it
    """

    def __init__(self, program: str, arguments: list[str], stdin: str | list[str] | None = None, stdin_file: str | None = None, environment: dict[str, str] | None = None):
        """Initialize command.

        Args:
            program: program to run
            arguments: list of arguments
            stdin: string or list of strings to pass as standard input
            stdin_file: file to use as standard input
            environment: dictionary with environment variables
        """

        self.program = program
        self.arguments = arguments
        self.environment = environment
        if stdin_file is not None and stdin is not None:
            raise RuntimeError("can't specify both stdin and stdin_file")
        self.stdin_file = stdin_file
        self.stdin = stdin
        if isinstance(stdin, list):
            self.stdin = "\n".join(stdin) + "\n"
        self.stdout = None
        self.stderr = None
        self.exit_code = None

    def run(self) -> bool:
        """Run the command.

        Returns:
            True if the command succeeded (exit code 0), False otherwise.
        """

        program = self.program if os.path.exists(self.program) else shutil.which(self.program)
        if program is None:
            raise RuntimeError(f"can't find program {self.program}")
        if self.stdin_file is not None:
            with open(self.stdin_file, "rb") as stdin:
                result = subprocess.run([program] + self.arguments, capture_output=True, check=False, stdin=stdin, env=self.environment)
        else:
            result = subprocess.run([program] + self.arguments, capture_output=True, check=False, input=self.stdin, env=self.environment)
        self.exit_code = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr.decode("utf-8") if isinstance(result.stderr, bytes) else result.stderr
        return self.exit_code == 0
