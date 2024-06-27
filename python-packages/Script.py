import argparse

import AssemblerOutput
import AtomicOutput
import Dependencies

class Script:
    def __init__(self, description, runlength_encode=False, assembler_output=False) -> None:
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.arg_parser.add_argument("-M", metavar="FILE", dest="depfile", help="output dependency information to FILE")
        self.arg_parser.add_argument("-o", metavar="FILE", dest="output", help="output to FILE")
        self.output = AtomicOutput.AtomicOutput()
        self.dependencies = None

        if runlength_encode:
            self.arg_parser.add_argument("-r", dest="runlength", action="store_true", help="runlength encode sprite data")

        self.assembler_output = assembler_output
        self.assembler = None

    def run(self):
        self.args = self.arg_parser.parse_args()

        self.output.set_filename(self.args.output)
        self.dependencies = Dependencies.Dependencies(self.args.depfile, self.args.output)
        self.output.run(lambda: self.execute())

    def execute(self):
        if self.assembler_output:
            self.assembler = AssemblerOutput.AssemblerOutput(self.output_file())
            self.assembler.header(self.args.file)
            self.assembler.data_section()
        self.execute_sub()

    def output_file(self):
        return self.output.get_file()
    
    def output_file_name(self):
        return self.output.get_file_name()

    def add_dependency(self, file):
        self.dependencies.add(file)
