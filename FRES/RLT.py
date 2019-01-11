from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.Padding import Padding
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryFile import BinaryFile
from .FresObject import FresObject


class Header(BinaryStruct):
    """RLT header."""
    magic  = b'_RLT'
    fields = (
        ('4s', 'magic'),
        ('I',  'unk04'), # offset of the RLT?
        ('I',  'unk08'), # 5
        ('I',  'unk0C'), # 0

        ('I',  'unk10'), # 0
        ('I',  'unk14'), # 0
        ('I',  'unk18'), # 0
        ('I',  'unk1C'), # D49E

        ('I',  'unk20'), # 0
        ('I',  'unk24'), # 3D
        ('I',  'unk28'), # 0
        ('I',  'unk2C'), # 0

        Offset32('data_start'),
    )
    size = 0x34


class RLT(FresObject):
    """A relocation table in an FRES."""

    def __init__(self, fres):
        self.fres = fres


    def readFromFRES(self, offset=None):
        """Read this object from the FRES."""
        if offset is None:
            offset = self.fres.header['rlt_offset']
        self.header = Header().readFromFile(self.fres.file, offset)
        self.dataStart = self.header['data_start']

        # XXX figure out the rest of this

        return self
