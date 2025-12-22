from Buffer import Buffer

# TODO: double check directory parsing

class Disk:
    """Class representing a virtual disk image."""

    class Track:
        def __init__(self, length):
            self.sectors = [None] * length
            self.errors = [0] * length
            self.free = [True] * length
            self.blocks_free = length

        def length(self):
            return len(self.sectors)
        
        def is_free(self, sector):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector} {self.length()}")
            return self.free[sector]
        
        def mark_used(self, sector):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            if self.is_free(sector):
                self.blocks_free -= 1
            self.free[sector] = False

        def mark_free(self, sector):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            if not self.is_free(sector):
                self.blocks_free += 1
            self.free[sector] = True

        def set_error(self, sector, error):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            self.errors[sector] = error

        def get_error(self, sector):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            return self.errors[sector]
        
        def has_errors(self):
            for error in self.errors:
                if error != 0:
                    return True
            return False

        def is_ok(self, sector):
            return self.get_error(sector) == 0

        def is_full(self):
            return self.blocks_free == 0
        
        def first_free(self):
            if self.is_full():
                return None
            for sector in range(self.length()):
                if self.is_free(sector):
                    return sector
            return None
        
        def next_free(self, sector, ignore_sector=None):
            if sector >= self.length():
                sector = sector % self.length()
                if sector > 0:
                    sector -= 1
            start_sector = sector
            while not self.is_free(sector) or sector == ignore_sector:
                sector += 1
                if sector >= self.length():
                    sector = 0
                if sector == start_sector:
                    return None
            return sector
        
        def encode_bam(self, buffer, size=3):
            buffer.add_byte(self.blocks_free)
            bam = 0
            for sector in self.sectors:
                bam = bam << 1 | (1 if sector is None else 0)
            buffer.add_int(bam, size)

        def write(self, sector, data, mark_used=True, error=0):
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            if len(data) != 256:
                raise RuntimeError(f"invalid block length {len(data)}")
            if mark_used:
                self.mark_used(sector)
            self.sectors[sector] = data
            self.errors[sector] = error

        def read(self, sector: int) -> bytes|None:
            if sector >= self.length():
                raise RuntimeError(f"invalid sector {sector}")
            if not self.is_ok(sector):
                # TODO: include error code name in exception
                raise RuntimeError(f"sector {sector} has read error {self.get_error(sector)}")
            return self.sectors[sector]

        def output(self, file):
            for sector in self.sectors:
                if sector is None:
                    file.write(b"\x00" * 256)
                else:
                    file.write(sector)
    
        def output_errors(self, file):
            for error in self.errors:
                file.write(error.to_bytes(1, byteorder="little"))

    class DirectoryEntry:
        def __init__(self, name:str|bytes, type:str, track:int, sector:int, blocks:int, closed:bool = True, locked:bool = False):
            if isinstance(name, str):
                name = name.encode("ascii", errors="replace")
            self.name = name
            self.type = type
            self.track = track
            self.sector = sector
            self.blocks = blocks
            self.closed = closed
            self.locked = locked
        
        def encode(self, buffer, track=0, sector=0):
            type_byte = Disk.file_types[self.type]
            if self.closed:
                type_byte |= 0x80
            if self.locked:
                type_byte |= 0x40
            buffer.add_byte(track)
            buffer.add_byte(sector)
            buffer.add_byte(type_byte)
            buffer.add_byte(self.track)
            buffer.add_byte(self.sector)
            buffer.add_data(self.name, 16, 0xa0)
            buffer.add_zeros(9)
            buffer.add_word(self.blocks)
            return
    
    class Zone:
        def __init__(self, tracks, sectors):
            self.tracks = tracks
            self.sectors = sectors
    
    class Layout:
        def __init__(self, zones, directory_tracks, dos_type, interleave, directory_interleave=None):
            self.zones = zones
            self.directory_tracks = directory_tracks
            self.dos_type = dos_type
            self.interleave = interleave
            if directory_interleave is None:
                self.directory_interleave = self.interleave
            else:
                self.directory_interleave = directory_interleave

        @property
        def tracks(self):
            total = 0
            for zone in self.zones:
                total += zone.tracks
            return total
        
        @property
        def sectors(self):
            total = 0
            for zone in self.zones:
                total += zone.tracks * zone.sectors
            return total
    
    layouts = {
        "d64": Layout([Zone(17, 21), Zone(7, 19), Zone(6, 18), Zone(5, 17)], [18], "2a", 10, 3),
        "d71": Layout([Zone(17, 21), Zone(7, 19), Zone(6, 18), Zone(5, 17), Zone(17, 21), Zone(7, 19), Zone(6, 18), Zone(5, 17)], [18, 53], "2a", 6, 3), 
        "d81": Layout([Zone(80, 40)], [40], "3d", 1)
    }
    file_types = {
        "del": 0x80,
        "prg": 0x82,
        "seq": 0x81,
        "usr": 0x84
    }

    def __init__(self, type:str|None = None, name:str = "", id:str = "", data:bytes|None = None):
        """Initialize disk image.
        
        Arguments:
            type: disk type (d64, d71, d81)
            name: disk name
            id: disk id
            data: existing disk image data
        """

        self.directory = []
        self.tracks = [Disk.Track(0)] # track indices start at 1
        self.errors = None
        self.name = b""
        self.id = b""
        self.layout = None

        if data is not None:
            if type is not None:
                raise RuntimeError("cannot specify both disk type and existing data")
            

            if len(data) % 256 == 0:
                blocks = len(data) // 256
                errors = False
            elif len(data) % 257 == 0:
                blocks = len(data) // 257
                errors = True
            else:
                raise RuntimeError("invalid disk image size")
            
            for layout in Disk.layouts.values():
                if layout.sectors == blocks:
                    self.layout = layout
                    break
            if self.layout is None:
                raise RuntimeError("unable to determine disk type")

            block = 0
            error_offset = blocks * 256

            for zone in self.layout.zones:
                for track_number in range(zone.tracks):
                    track = Disk.Track(zone.sectors)
                    self.tracks.append(track)
                    for sector_number in range(zone.sectors):
                        sector_data = data[block * 256:(block + 1) * 256]
                        if errors:
                            error_byte = data[error_offset + block]
                        else:
                            error_byte = 0

                        track.write(sector_number, sector_data, mark_used=False, error=error_byte)
                        block += 1
            
            self.parse_directory()

        else:
            if type is None:
                raise RuntimeError("must specify disk type when not loading existing data")

            if type not in Disk.layouts:
                raise RuntimeError(f"unknown disk type '{type}'")
            self.layout = Disk.layouts[type]
            for zone in self.layout.zones:
                for track in range(zone.tracks):
                    self.tracks.append(Disk.Track(zone.sectors))
            self.set_name(name, id)

    def set_name(self, name:str|bytes, id:str|bytes) -> None:
        """Set disk name and id.

        Arguments:
            name: disk name
            id: disk id
        """

        if isinstance(name, str):
            name = name.encode("ascii", errors="replace")
        if len(name) > 16:
            raise RuntimeError(f"disk name '{name}' is too long")
        self.name = name
        if isinstance(id, str):
            id = id.encode("ascii", errors="replace")
        if len(id) <= 2:
            self.id = id + b" " * (3 - len(id)) + self.layout.dos_type.encode("ascii")
        elif len(id) > 5:
            raise RuntimeError(f"disk id '{id}' too long")
        else:
            self.id = id


    def add_del(self, name:str) -> None:
        """Add deleted file entry to directory.

        Arguments:
            name: file name
        """

        if len(name) > 16:
            raise RuntimeError(f"file name '{name}' is too long")
        self.directory.append(Disk.DirectoryEntry(name, "del", 0, 0, 0))
    
    def add_file(self, name:str, data:bytes, type:str = "prg") -> None:
        """Add file to disk image.

        Arguments:
            name: file name
            data: file data
            type: file type (prg, seq, usr, del)
        """

        if len(name) > 16:
            raise RuntimeError(f"file name '{name}' is too long")
        if type not in Disk.file_types:
            raise RuntimeError(f"unknown file type '{type}'")
        (track, sector, blocks) = self.add_file_data(data)
        self.directory.append(Disk.DirectoryEntry(name, "prg", track, sector, blocks))

    def add_block(self, track:int, sector:int, data:bytes) -> None:
        """Add block data to given track and sector.

        Arguments:
            track: track number
            sector: sector number
            data: block data (256 bytes)
        """

        if track <= 0 or track > self.num_tracks():
            raise RuntimeError(f"invalid track {track}")
        if sector < 0 or sector >= self.tracks[track].length():
            raise RuntimeError(f"invalid sector {sector}")
        if len(data) != 256:
            raise RuntimeError(f"invalid block length {len(data)}")
        if not self.tracks[track].is_free(sector):
            raise RuntimeError(f"block {track},{sector} already used")
        self.tracks[track].write(sector, data)
    
    def output(self, file) -> None:
        """Write disk image to file.

        Arguments:
            file: file object to write to
        """

        self.encode_directory()
        self.encode_bam()
        for track in self.tracks[1:]:
            track.output(file)

        if self.has_errors():
            for track in self.tracks[1:]:
                track.output_errors(file)

    def has_errors(self) -> bool:
        """Check whether disk has any read errors.

        Returns:
            True if disk has read errors, False otherwise
        """

        for track in self.tracks[1:]:
            if track.has_errors():
                return True
        return False
    
    def read_file(self, name:str|bytes) -> bytes:
        """Read file data from disk image.

        Arguments:
            name: file name
        Returns:
            file data
        """

        if isinstance(name, str):
            name = name.encode("ascii", errors="replace")

        entry = None
        for e in self.directory:
            if e.name == name:
                entry = e
                break
        if entry is None:
            raise RuntimeError(f"file '{name}' not found on disk")

        data = bytearray()
        track = entry.track
        sector = entry.sector

        while track != 0:
            block_data = self.tracks[track].read(sector)
            if block_data is None:
                raise RuntimeError(f"unable to read block {track},{sector}")
            next_track = block_data[0]
            next_sector = block_data[1]
            if next_track == 0:
                end = block_data[1] + 1
                data += block_data[2:end]
            else:
                data += block_data[2:]
            (track, sector) = (next_track, next_sector)

        return bytes(data)

    # private methods

    def add_file_data(self, data):
        blocks = [data[i:i + 254] for i in range(0, len(data), 254)]
        (start_track, start_sector) = self.find_first_block()
        (track, sector) = (start_track, start_sector)
        for block in blocks[:-1]:
            (next_track, next_sector) = self.find_next_block(track, sector)
            if next_track is None:
                raise RuntimeError("disk full")
            self.add_block(track, sector, self.encode_track_sector(next_track, next_sector, block))
            (track, sector) = (next_track, next_sector)
        else:
            block = blocks[-1]
            self.add_block(track, sector, self.encode_track_sector(0, len(block) + 1, block))

        return (start_track, start_sector, len(blocks))

    def encode_track_sector(self, track, sector, data):
        buffer = Buffer()
        buffer.add_byte(track)
        buffer.add_byte(sector)
        buffer.add_data(data, 254)
        return buffer.data

    def find_first_block(self):
        track = self.layout.directory_tracks[0]
        distance = 1
        while track - distance > 0 or track + distance <= self.num_tracks():
            if track - distance > 0:
                sector = self.tracks[track - distance].first_free()
                if sector is not None:
                    return (track - distance, sector)
            if track + distance <= self.num_tracks():
                sector = self.tracks[track + distance].first_free()
                if sector is not None:
                    return (track + distance, sector)
            distance += 1            
        return (None, None)
    
    def find_next_block(self, track, sector):
        start_track = track
        if track < self.layout.directory_tracks[0]:
            direction = -1
        else:
            direction = 1
        changed_direction = False

        while True:
            next_sector = self.tracks[track].next_free(sector + self.layout.interleave, sector if track == start_track else None)
            if next_sector is not None:
                return (track, next_sector)
            track += direction
            if track < 1 or track > self.num_tracks():
                if changed_direction:
                    return (None, None)
                changed_direction = True
                direction *= -1
                track = self.layout.directory_tracks[0] + direction
    
    def find_first_directory_block(self):
        if self.layout.directory_tracks[0] == 40:
            return (self.layout.directory_tracks[0], 3)
        else:
            return (self.layout.directory_tracks[0], 1)
        
    def find_next_directory_block(self, track, sector):
        start_track = track
        index = self.layout.directory_tracks.index(track)
        for index in range(self.layout.directory_tracks.index(track), len(self.layout.directory_tracks)):
            track = self.layout.directory_tracks[index]
            next_sector = self.tracks[track].next_free(sector + self.layout.directory_interleave, sector if track == start_track else None)
            if next_sector is not None:
                return (track, next_sector)
        return None

    def encode_directory(self):
        blocks = [self.directory[i:i + 8] for i in range(0, len(self.directory), 8)]

        (track, sector) = self.find_first_directory_block()
        for block in blocks[:-1]:
            (next_track, next_sector) = self.find_next_directory_block(track, sector)
            if next_track is None:
                raise RuntimeError("directory full")
            self.encode_directory_block(track, sector, block, next_track, next_sector)
            (track, sector) = (next_track, next_sector)
        else:
            self.encode_directory_block(track, sector, blocks[-1])
    
    def encode_directory_block(self, track, sector, entries, next_track=0, next_sector=255):
        buffer = Buffer()
        entries[0].encode(buffer, next_track, next_sector)
        for entry in entries[1:]:
            entry.encode(buffer)
        buffer.pad(256)
        self.add_block(track, sector, buffer.data)


    def encode_bam(self):
        buffer = Buffer()
        (track, sector) = self.find_first_directory_block()
        buffer.add_byte(track)
        buffer.add_byte(sector)
        buffer.add_data(self.layout.dos_type[-1].upper())
        buffer.add_byte(self.is_double_sided())
        if self.num_tracks() <= 70:
            for track in self.tracks[1:36]:
                track.encode_bam(buffer)
        buffer.add_data(self.name, 16, 0xa0)
        buffer.add_word(0xa0a0)
        buffer.add_data(self.id)
        buffer.add_word(0xa0a0)
        if self.num_tracks() <= 70:
            buffer.add_word(0xa0a0)
        if self.is_double_sided():
            buffer.pad(0xdd)
            for track in self.tracks[36:]:
                buffer.add_byte(track.blocks_free)
        buffer.pad(256)
        self.add_block(self.layout.directory_tracks[0], 0, buffer.data)

        if self.is_double_sided():
            buffer.clear()
            for track in self.tracks[36:]:
                track.encode_bam(buffer)
            buffer.pad(256)
            self.add_block(self.layout.directory_tracks[1], 0, buffer.data)
        elif self.num_tracks() > 70:
            dos_version = bytearray(self.layout.dos_type[-1].upper(), "utf-8")[0]
            for side in range(0, 2):
                buffer.clear()
                if side == 0:
                    buffer.add_byte(self.layout.directory_tracks[0])
                    buffer.add_byte(2)
                else:
                    buffer.add_byte(0)
                    buffer.add_byte(255)
                buffer.add_byte(dos_version)
                buffer.add_byte(dos_version ^ 0xff)
                buffer.add_data(self.id[0:2])
                buffer.add_byte(0xc0) # I/O byte
                buffer.add_byte(0) # auto-boot-loader flag
                buffer.pad(16)
                start_track = side * 40 + 1
                for track in self.tracks[start_track:start_track+40]:
                    track.encode_bam(buffer, 5)
                self.add_block(self.layout.directory_tracks[0], side + 1, buffer.data)

    def parse_directory(self):
        # read disk name and id from BAM
        bam_track = self.layout.directory_tracks[0]
        bam_sector = 0
        bam_data = self.tracks[bam_track].read(bam_sector)
        if bam_data is None:
            raise RuntimeError("unable to read BAM sector")
        self.name = bam_data[0x90:0xa0].rstrip(b"\xa0")
        self.id = bam_data[0xa2:0xa7].rstrip(b"\xa0")

        # TODO: mark used blocks from BAM

        # read directory entries
        (track, sector) = self.find_first_directory_block()
        while track != 0:
            dir_data = self.tracks[track].read(sector)
            if dir_data is None:
                raise RuntimeError("unable to read directory sector")
            next_track = dir_data[0]
            next_sector = dir_data[1]
            for i in range(8):
                entry_offset = i * 32
                entry_type = dir_data[entry_offset + 2]
                if entry_type == 0:
                    continue
                # TODO: remember closed, locked, handle unknown types
                file_type = "???"
                for ft, code in Disk.file_types.items():
                    if code == (entry_type & 0x07) | 0x80:
                        file_type = ft
                        break
                name = dir_data[entry_offset + 5:entry_offset + 21].rstrip(b"\xa0") # TODO: end at first 0xa0
                entry = Disk.DirectoryEntry(
                    name,
                    file_type,
                    dir_data[entry_offset + 3],
                    dir_data[entry_offset + 4],
                    int.from_bytes(dir_data[entry_offset + 30:entry_offset + 32], byteorder="little"),
                    closed = (entry_type & 0x80) != 0,
                    locked = (entry_type & 0x40) != 0
                )
                self.directory.append(entry)
            (track, sector) = (next_track, next_sector)

    def is_double_sided(self):
        return self.num_tracks() == 70
    
    def num_tracks(self):
        return len(self.tracks) - 1
    