import os
import shutil
import subprocess


class Command:
    def __init__(self, program, arguments, stdin=None, stdin_file=None, environment=None):
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
