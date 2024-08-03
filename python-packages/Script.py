import argparse
import enum
import os
import sys

import AssemblerOutput
import AtomicOutput
import Dependencies

class Option(enum.Enum):
    name = enum.auto()
    alignment = enum.auto()
    assembler_output = enum.auto()
    section = enum.auto()
    runlength_encode = enum.auto()
    include_directories = enum.auto()

    # collections
    assembler = enum.auto()
    symbol = enum.auto()

collection_options = {
    Option.assembler: {Option.section},
    Option.symbol: {Option.assembler, Option.name, Option.alignment}
}

class Options:
    def __init__(self, *args) -> None:
        self.options = set()
        # I have NO idea why I have to iterate this twice.
        for options in args:
            for option in options:
                self.add(option)

    def add(self, option):
        if option in collection_options:
            for sub_option in collection_options[option]:
                self.add(sub_option)
        else:
            self.options.add(option)
        
    def is_set(self, option):
        return option in self.options

class Script:
    # Public API

    def __init__(self, description, *options) -> None:
        self.options = Options(options)
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.arg_parser.add_argument("-M", metavar="FILE", dest="depfile", help="output dependency information to FILE")
        self.arg_parser.add_argument("-o", metavar="FILE", dest="output_filename", help="write output to FILE")
        self.output = AtomicOutput.AtomicOutput()
        self.dependencies = None

        if self.options.is_set(Option.alignment):
            self.arg_parser.add_argument("-a", "--alignment", metavar="ALIGNMENT", dest="alignment", help="align to ALIGNMENT")
        if self.options.is_set(Option.include_directories):
            self.arg_parser.add_argument("-I", metavar="DIRECTORY", dest="include_directories", default=[], action="append", help="search for files in DIRECTORY")
        if self.options.is_set(Option.name):
            self.arg_parser.add_argument("-n", "--name", metavar="NAME", dest="symbol_name", help="define symbol NAME")
        if self.options.is_set(Option.runlength_encode):
            self.arg_parser.add_argument("-r", "--runlength", dest="runlength", action="store_true", help="runlength encode data")
        if self.options.is_set(Option.section):
            self.arg_parser.add_argument("-s", "--section", metavar="SECTION", dest="section", help="put in SECTION")

        self.assembler = None

    def run(self):
        try:
            self.args = self.arg_parser.parse_args()

            self.prepare()

            self.output.set_filename(self.output_filename())
            self.dependencies = Dependencies.Dependencies(self.args.depfile, self.output_filename())
            if not self.output.run(lambda: self.execute()):
                sys.exit(1)
        except Exception as ex:
            print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
            sys.exit(1)
        


    # Subclass API
    # Functions called by subclass.

    # Add FILE as dependency.
    def add_dependency(self, file):
        self.dependencies.add(file)
    
    # Find FILE.
    def find_file(self, file, optional=False):
        if not os.path.exists(file):
            found = False
            for directory in [os.path.dirname(self.input_filename())] + self.args.include_directories:
                new_file = os.path.join(directory, file)
                if os.path.exists(new_file):
                    file = new_file
                    found = True
                    break
            if not found:
                if optional:
                    return None
                else:
                    raise RuntimeError(f"can't find {file}")
        self.add_dependency(file)
        return file


    # Get filename of final output file.
    def output_filename(self):
        if self.args.output_filename is not None:
            return self.args.output_filename
        return self.default_output_filename()

    # Get temporary output file
    def output_file(self):
        return self.output.get_file()
    
    # Get filename of temporary output file.
    def output_file_name(self):
        return self.output.get_filename()

    # Get name of assembler symbol.
    def symbol_name(self):
        if self.args.name is not None:
            return self.args.name
        # TODO: remove invalid characters
        return os.path.splitext(self.input_filename())[0].replace("-", "_")


    # Required Subclass Methods

    # Do actual processing.
    # execute_sub(self)


    # Optional Subclass Metods

    # Get default filename extension for output files. Used by default implementation of `default_output_filename()`.
    def default_output_extension(self):
        return "s"

    # Validate arguments and other preparations. Run before output file is created.
    def prepare(self):
        pass


    # Overridable Methods

    # Get filename of input file.
    def input_filename(self):
        return self.args.file
    
    # Get filename of final output file if not specified via `-o` command line option.
    def default_output_filename(self):
        name, extension = os.path.splitext(self.input_filename())
        return os.path.basename(name) + "." + self.default_output_extension()


    # Internal Methods

    # Set up and call actual processing.
    def execute(self):
        if self.options.is_set(Option.assembler_output):
            self.assembler = AssemblerOutput.AssemblerOutput(self.output_file())
            self.assembler.header(self.input_filename())
            self.assembler.data_section()
        self.execute_sub()
        self.dependencies.write()
