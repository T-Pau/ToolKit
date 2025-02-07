import enum


import Buffer

class Computer(enum.Enum):
    C64 = "C64"
    C128 = "C128"
    VIC20 = "VIC20"
    PLUS4 = "PLUS4"

class CartridgeType(enum.Enum):
    EASYFLASH = 32
    MAGIC_DESK = 19
    MAGIC_DESK_C128 = 4
    MAGIC_DESK_C264 = 1

class ChipType(enum.Enum):
    ROM = 0
    RAM = 1
    FLASH = 2
    EEPROM = 3

class CRT:
    class Type:
        def __init__(self, type, computer, exrom=False, game=False):
            self.type = type
            self.computer = computer
            self.exrom = exrom
            self.game = game

    class Chip:
        def __init__(self, data, address, type=ChipType.ROM, bank=0, size=None):
            self.type = type
            self.bank = bank
            self.address = address
            self.data = data
            if size is None:
                self.size = len(data)
            elif size < len(data):
                raise RuntimeError(f"chip data size {len(data)} too large for chip size {size}")
            else:
                self.size = size
            
        def output(self, file):
            buffer = Buffer.Buffer(padding=0xff, byteorder="big")
            buffer.add_data("CHIP")
            buffer.add_long(self.size + 0x10)
            buffer.add_word(self.type.value)
            buffer.add_word(self.bank)
            buffer.add_word(self.address)
            buffer.add_word(self.size)
            buffer.add_data(self.data, self.size)
            buffer.output(file)

    types = {
        "EasyFlash": Type(CartridgeType.EASYFLASH, Computer.C64, game=True),
        "Magic Desk": Type(CartridgeType.MAGIC_DESK, Computer.C64, exrom=True),
        "Magic Desk C128": Type(CartridgeType.MAGIC_DESK_C128, Computer.C128),
        "Magic Desk C264": Type(CartridgeType.MAGIC_DESK_C264, Computer.PLUS4)
    }

    def __init__(self, type_name, name):
        if type_name not in CRT.types:
            raise RuntimeError(f"unknown CRT type '{type_name}'")
        self.type = CRT.types[type_name]
        self.name = name
        self.chips = []

    def add_chip(self, data, address, type=ChipType.ROM, bank=0, size=None):
        self.chips.append(CRT.Chip(data, address, type, bank, size))
    
    def output(self, file):
        self.output_header(file)
        for chip in self.chips:
            chip.output(file)
        
    def output_header(self, file):
        buffer = Buffer.Buffer(byteorder="big")
        buffer.add_data(self.type.computer.value + " CARTRIDGE", length=16, padding=0x20)
        buffer.add_long(0x40)
        if self.type.computer == Computer.C64:
            buffer.add_word(0x0100)
        else:
            buffer.add_word(0x0200)
        buffer.add_word(self.type.type.value)
        buffer.add_byte(0 if self.type.exrom else 1)
        buffer.add_byte(0 if self.type.game else 1)
        buffer.pad(0x20)
        buffer.add_data(self.name, padding=0x20, length=32)
        buffer.output(file)
