"""
  Script -- implement reliable scripts with standard interface
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

import argparse
import enum
import os
import re
import sys
import traceback
from typing import Any, IO

import AssemblerOutput
import AtomicOutput
import Dependencies
import FileReader
import RunlengthEncoder

class Option(enum.Enum):
    symbol_name = enum.auto()
    alignment = enum.auto()
    assembler_output = enum.auto()
    binary_output = enum.auto()
    defines = enum.auto()
    dyndep = enum.auto()
    file_reader = enum.auto()
    file_reader_preprocessor = enum.auto()
    include_directories = enum.auto()
    runlength_encode = enum.auto()
    section = enum.auto()

    # collections
    assembler = enum.auto()
    preprocessor = enum.auto()
    symbol = enum.auto()

collection_options = {
    Option.assembler: {Option.section, Option.assembler_output},
    Option.preprocessor: {Option.defines, Option.file_reader, Option.file_reader_preprocessor},
    Option.symbol: {Option.assembler, Option.symbol_name, Option.alignment}
}

class Options:
    def __init__(self, *args) -> None:
        self.options = set()
        # I have NO idea why I have to iterate this twice.
        for options in args:
            for option in options:
                self.add(option)

    def add(self, option: set[Option]) -> None:
        if option in collection_options:
            for sub_option in collection_options[option]:
                self.add(sub_option)
        else:
            self.options.add(option)

    def is_set(self, option: Option) -> bool:
        return option in self.options

class Script:
    # Public API
    def __init__(self, description: str, *options: Option) -> None:
        self.options = Options(options)
        self.arg_parser = argparse.ArgumentParser(description=description, allow_abbrev=False)
        self.arg_parser.add_argument("-M", metavar="FILE", dest="depfile", help="output dependency information to FILE")
        self.arg_parser.add_argument("-o", metavar="FILE", dest="output_filename", help="write output to FILE")
        self.output = AtomicOutput.AtomicOutput()
        self.dependencies = None
        self.assembler = None
        self.file_reader = None
        self.dyndep_mode = False
        self.built_files = set()

        if self.options.is_set(Option.alignment):
            if self.natural_alignment() is not None:
                self.arg_parser.add_argument("--align", const=self.natural_alignment(), action="store_const", dest="alignment", help=f"align to {self.natural_alignment()}")
            self.arg_parser.add_argument("-a", "--alignment", default=None, metavar="ALIGNMENT", dest="alignment", help="align to ALIGNMENT")

        if self.options.is_set(Option.defines):
            self.arg_parser.add_argument("-D", action="append", dest="defines")

        if self.options.is_set(Option.dyndep):
            self.arg_parser.add_argument("--dyndep", metavar="FILE", dest="dyndep", help="output dynamic dependencies to FILE.")
            self.arg_parser.add_argument("--built-files", metavar="FILE", dest="built_files", help="read list of built files from FILE.")

        if self.options.is_set(Option.include_directories):
            self.arg_parser.add_argument("-I", metavar="DIRECTORY", dest="include_directories", default=[], action="append", help="search for files in DIRECTORY")

        if self.options.is_set(Option.symbol_name):
            self.arg_parser.add_argument("-n", "--name", metavar="NAME", dest="name", help="define symbol NAME")

        if self.options.is_set(Option.runlength_encode):
            self.arg_parser.add_argument("-r", "--runlength", dest="runlength", action="store_true", help="runlength encode data")

        if self.options.is_set(Option.section):
            self.arg_parser.add_argument("-s", "--section", metavar="SECTION", dest="section", default="data", help="put in SECTION")

    def run(self) -> None:
        try:
            self.args = self.arg_parser.parse_args()

            if self.options.is_set(Option.dyndep) and self.args.dyndep:
                self.dyndep_mode = True
                self.output.set_filename(self.args.dyndep)
                self.read_built_files()
                if not self.output.run(lambda: self.create_dyndep()):
                    sys.exit(1)
            else:
                self.prepare()

                self.output.set_filename(self.output_filename(), self.options.is_set(Option.binary_output))
                self.dependencies = Dependencies.Dependencies(self.args.depfile, self.output_filename())
                if not self.output.run(lambda: self.execute()):
                    sys.exit(1)
                self.dependencies.check()
        except Exception as ex:
            if "TOOLKIT_DEBUG" in os.environ:
                traceback.print_exception(ex)
            elif str(ex) != "":
                print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
            sys.exit(1)
        


    # Subclass API
    # Functions called by subclass.

    # Add FILE as dependency.
    def add_dependency(self, file: str) -> None:
        if self.dependencies is not None:
            self.dependencies.add(file)
    
    # Print error.
    def error(self, message: str) -> None:
        self.output.error(message)

    # Find FILE.
    def find_file(self, file: str, optional: bool = False) -> str | None:
        search_include_directories = not (os.path.isabs(file) or file.startswith("./")) and self.options.is_set(Option.include_directories)
        file = os.path.normpath(file)
        found = False
        if not search_include_directories:
            found = os.path.exists(file)
        else:
            found = False
            relative_directories = []
            filename = self.input_filename()
            if filename is not None:
                relative_directories = [os.path.dirname(filename)]
            for directory in relative_directories + self.args.include_directories:
                new_file = os.path.normpath(os.path.join(directory, file))
                if self.file_exists(new_file):
                    file = new_file
                    found = True
                    break
        if not found:
            if optional:
                return None
            else:
                raise RuntimeError(f"can't find file '{file}'")
        self.add_dependency(file)
        return file

    def symbol(self, binary: bytes, name_suffix: str = "") -> None:
        alignment = None
        if self.args.runlength:
            runlength = RunlengthEncoder.RunlengthEncoder()
            runlength.add_bytes(binary)
            binary = runlength.end()
        if self.args.alignment is not None:
            alignment = int(self.args.alignment)

        self.assembler.bytes_object(self.symbol_name()+name_suffix, binary, section=self.args.section, alignment=alignment)


    # Get filename of final output file.
    def output_filename(self) -> str:
        if self.args.output_filename is not None:
            return self.args.output_filename
        return self.default_output_filename()

    # Get temporary output file
    def output_file(self) -> IO[Any]:
        return self.output.get_file()
    
    # Get filename of temporary output file.
    def output_file_name(self) -> str:
        return self.output.get_filename()

    # Get name of assembler symbol.
    def symbol_name(self) -> str:
        if self.args.name is not None:
            return self.args.name
        filename = self.input_filename()
        if filename is None:
            raise RuntimeError("no name or input file specified")
        # TODO: remove invalid characters
        return os.path.splitext(filename)[0].replace("-", "_")


    # Required Subclass Methods

    # Do actual processing.
    # execute_sub(self)

    # Get list of dependencies for dynamic dependency discovery (only needed if dyndep option is set)
    # get_dynamic_dependencies(self)

    # Optional Subclass Metods

    # Get default filename extension for output files. Used by default implementation of `default_output_filename()`.
    def default_output_extension(self) -> str:
        return "s"

    # Alignment to use if --align option is given.
    def natural_alignment(self) -> int | None:
        return None

    # Validate arguments and other preparations. Run before output file is created.
    def prepare(self) -> None:
        pass


    # Overridable Methods

    # Get filename of input file.
    def input_filename(self) -> str | None:
        return self.args.file
    
    # Get filename of final output file if not specified via `-o` command line option.
    def default_output_filename(self) -> str:
        filename = self.input_filename()
        if filename is None:
            raise RuntimeError("no output or input file name specified")
        name, extension = os.path.splitext(filename)
        return os.path.basename(name) + "." + self.default_output_extension()

    # Excute actual processing.
    def execute_sub(self) -> None:
        pass

    def get_dynamic_dependencies(self) -> list[str]:
        return []

    # Internal Methods

    # Set up and call actual processing.
    def execute(self) -> None:
        if self.options.is_set(Option.assembler_output):
            self.assembler = AssemblerOutput.AssemblerOutput(self.output_file())
            self.assembler.header(self.input_filename())
            self.assembler.section(self.args.section)
        self.common_preparations()
        self.execute_sub()
        if self.file_reader is not None and not self.file_reader.ok:            
            self.output.fail()
        if self.dependencies is not None:
            self.dependencies.write()
            self.dependencies.check()
    
    def create_dyndep(self) -> None:
        self.common_preparations()
        dependencies = self.get_dynamic_dependencies()
        if self.file_reader is not None and not self.file_reader.ok:            
            self.output.fail()
        # TODO: quote spaces &c
        quoted_dependencies = [re.sub(r'([ :\n$])', r'$\1', s) for s in dependencies]
        dependencies_string = " ".join(quoted_dependencies)
        print("ninja_dyndep_version = 1", file=self.output_file())
        print(f"build {self.output_filename()} : dyndep | {dependencies_string}", file=self.output_file())

    def common_preparations(self) -> None:
        if self.options.is_set(Option.file_reader):
            preprocess = self.options.is_set(Option.file_reader_preprocessor)
            if preprocess and self.options.is_set(Option.defines):
                defines = self.args.defines
            else:
                defines = {}
            self.file_reader = FileReader.FileReader(self, self.input_filename(), preprocess=preprocess, defines=defines)

    def read_built_files(self) -> None:
        filename = self.find_file(self.args.built_files)
        if filename is None:
            raise RuntimeError("built files list not found")
        for line in open(filename, "r"):
            self.built_files.add(line.rstrip("\n"))

    def file_exists(self, file: str) -> bool:
        if file in self.built_files:
            return True
        else:
            return os.path.exists(file)
