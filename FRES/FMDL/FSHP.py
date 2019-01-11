from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.Padding import Padding
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryFile import BinaryFile
from io_scene_bfres.FRES.FresObject import FresObject
from io_scene_bfres.FRES.Dict import Dict
from .Attribute import Attribute, AttrStruct
from .Buffer    import Buffer
from .FVTX      import FVTX
from .LOD       import LOD
from .Vertex    import Vertex
import struct


class Header(BinaryStruct):
    """FSHP header."""
    magic  = b'FSHP'
    fields = (
        ('4s', 'magic'),
        ('3I', 'unk04'),
        String('name'), Padding(4),

        Offset64('fvtx_offset'), # => FVTX

        Offset64('lod_offset'), # => LOD models
        Offset64('fskl_idx_array_offs'), # => 00030002 00050004 00070006 00090008  000B000A 000D000C 000F000E 00110010

        Offset64('unk30'), # 0
        Offset64('unk38'), # 0

        # bounding box and bounding radius
        Offset64('bbox_offset'), # => ~24 floats / 8 Vec3s / 6 Vec4s
        Offset64('bradius_offset'), # => => 3F03ADA8 3EFC1658 00000000 00000D14  00000000 00000000 00000000 00000000
            # as floats:
            # 3F03ADA8 = 0.5143685340881348
            # 3EFC1658 = 0.4923579692840576

        Offset64('unk50'),
        ('I',    'flags'),
        ('H',    'index'),
        ('H',    'fmat_idx'),

        ('H',    'single_bind'),
        ('H',    'fvtx_idx'),
        ('H',    'skin_bone_idx_cnt'),
        ('B',    'vtx_skin_cnt'),
        ('B',    'lod_cnt'),
        ('I',    'vis_group_cnt'),
        ('H',    'fskl_array_cnt'),
        Padding(2),
    )
    size = 0x70


class FSHP(FresObject):
    """A shape object in an FRES."""
    Header = Header

    def __init__(self, fres):
        self.fres         = fres
        self.fvtx         = None
        self.lods         = None
        self.header       = None
        self.headerOffset = None


    def __str__(self):
        return "<FSHP(@%s) at 0x%x>" %(
            '?' if self.headerOffset is None else hex(self.headerOffset),
            id(self),
        )


    def dump(self):
        """Dump to string for debug."""
        res  = []
        res.append("Flags: 0x%08X" % self.header['flags'])
        res.append("Idx: 0x%04X" % self.header['index'])
        res.append("FmatIdx: 0x%04X" % self.header['fmat_idx'])
        res.append("SingleBind: 0x%04X" % self.header['single_bind'])
        res.append("LODs: %3d" % len(self.lods))
        res = ', '.join(res)
        #return '\n'.join(res).replace('\n', '\n      ')
        return res


    def readFromFRES(self, offset=None):
        """Read this object from given file."""
        if offset is None: offset = self.fres.file.tell()
        print("Reading FSHP from 0x%06X" % offset)
        self.headerOffset = offset
        self.header = self.fres.read(Header(), offset)
        self.name   = self.header['name']

        # read FVTX
        self.fvtx = FVTX(self.fres).readFromFRES(
            self.header['fvtx_offset'])

        # read LODs
        self.lods = []
        offs = self.header['lod_offset']
        for i in range(self.header['lod_cnt']):
            model = LOD(self.fres).readFromFRES(offs)
            offs += LOD.Header.size
            self.lods.append(model)

        return self
