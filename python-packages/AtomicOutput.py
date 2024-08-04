import os
import sys
import traceback


class AtomicOutput:
    def __init__(self):
        self.filename = None
        self.only_if_changed = False
        self.temp_name = None
        self.file = None
        self.ok = True

    def set_filename(self, filename):
        if self.file is not None:
            raise RuntimeError("can't change output filename after opening file")
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
            self.file = open(self.get_filename(), "w")
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
        if self.temp_name:
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
