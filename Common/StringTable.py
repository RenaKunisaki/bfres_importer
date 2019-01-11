from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.Padding import Padding
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryFile import BinaryFile


class Header(BinaryStruct):
    """String Table header."""
    magic  = b'_STR'
    fields = (
        ('4s', 'magic'),    Padding(4),
        ('I',  'size'),     Padding(4),
        ('I',  'num_strs'),
    )
    size = 0x14


class StringTable:
    """A string table in an FRES."""
    Header = Header

    def __init__(self):
        self.strings = {}


    def readFromFile(self, file, offset=None):
        """Read this object from the given file."""

        #print("Read str table from 0x%X" % offset)
        header = self.Header()
        self.header = header.readFromFile(file, offset)
        offset += header.size

        for i in range(self.header['num_strs']):
            offset += (offset & 1) # pad to u16
            length = file.read('<H',   offset)
            data   = file.read(length, offset+2)
            try:
                data = data.decode('shift-jis')
            except UnicodeDecodeError:
                print("FRES: Can't decode string from 0x%X as 'shift-jis': %s" %
                    (offset, data[0:16]))
                raise
            self.strings[offset] = data
            #print('StrTab[%06X]: "%s"' % (offset, data))
            offset += length + 3 # +2 for length, 1 for null terminator

        return self
