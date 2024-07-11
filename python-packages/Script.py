import argparse
import os
import sys

import AssemblerOutput
import AtomicOutput
import Dependencies

class Options:
    def __init__(self, assembler_output=False, runlength_encode=False, symbol_name=False) -> None:
        self.assembler_output = assembler_output
        self.runlength_encode = runlength_encode
        self.symbol_name = symbol_name

class Script:
    # Public API

    def __init__(self, description, options = Options()) -> None:
        self.options = options
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.arg_parser.add_argument("-M", metavar="FILE", dest="depfile", help="output dependency information to FILE")
        self.arg_parser.add_argument("-o", metavar="FILE", dest="output_filename", help="write output to FILE")
        self.output = AtomicOutput.AtomicOutput()
        self.dependencies = None

        if self.options.runlength_encode:
            self.arg_parser.add_argument("-r", dest="runlength", action="store_true", help="runlength encode data")
        if self.options.symbol_name:
            self.arg_parser.add_argument("-n", metavar="NAME", dest="symbol_name", help="define symbol NAME")

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

    # Add FILE as dependency.
    def add_dependency(self, file):
        self.dependencies.add(file)
    
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
        return self.output.get_file_name()

    # Get name of assembler symbol.
    def symbol_name(self):
        if self.args.symbol_name is not None:
            return self.args.symbol_name
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
        if self.options.assembler_output:
            self.assembler = AssemblerOutput.AssemblerOutput(self.output_file())
            self.assembler.header(self.input_filename())
            self.assembler.data_section()
        self.execute_sub()
        self.dependencies.write()
