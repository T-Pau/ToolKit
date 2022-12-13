import os
import sys


class AtomicOutput:
    def __init__(self):
        self.filename = None
        self.only_if_changed = False
        self.temp_name = None
        self.file = None

    def set_filename(self, filename):
        if self.file is not None:
            raise RuntimeError("can't change output filename after opening file")
        self.filename = filename

    def set_only_if_changed(self, value):
        if self.file is not None:
            raise RuntimeError("can't change only-if-changed after opening file")
        self.only_if_changed = value

    def get_file(self):
        if self.file is None:
            if self.only_if_changed:
                self.temp_name = self.filename + "XXX"  # TODO: make unique name with pid
                self.file = open(self.temp_name, "w")
            else:
                self.file = open(self.filename, "w")
        return self.file

    def abort(self, message):
        print(f"{sys.argv[0]}: {message}", file=sys.stderr)
        self.discard()
        exit(1)

    def close(self):
        if self.file is not None:
            self.file.close()
            # if self.only_if_changed: # TODO: move temp_name to filename

    def discard(self):
        if self.file is not None:
            self.file.close()
            if self.only_if_changed:
                os.remove(self.temp_name)
            else:
                os.remove(self.filename)
