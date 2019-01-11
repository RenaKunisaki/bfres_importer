from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.Padding import Padding
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryFile import BinaryFile
from io_scene_bfres.FRES.FresObject import FresObject
from io_scene_bfres.FRES.Dict import Dict
from .Attribute import Attribute, AttrStruct
from .Buffer import Buffer
from .Vertex import Vertex
import struct


class Header(BinaryStruct):
    """FVTX header."""
    magic  = b'FVTX'
    fields = (
        ('4s', 'magic'),
        ('3I', 'unk04'),
        Offset64('vtx_attrib_array_offs'),
        Offset64('vtx_attrib_dict_offs'),
        Offset64('unk10'),
        Offset64('unk18'),
        Offset64('unk20'),
        Offset64('vtx_bufsize_offs'),
        Offset64('vtx_stridesize_offs'),
        Offset64('vtx_buf_array_offs'),
        Offset32('vtx_buf_offs'),
        ('B',  'num_attrs'),
        ('B',  'num_bufs'),
        ('H',  'index'), # Section index: index into FVTX array of this entry.
        ('I',  'num_vtxs'),
        ('I',  'skin_weight_influence'),
    )
    size = 0x60


class FVTX(FresObject):
    """A vertex buffer in an FRES."""
    Header = Header

    def __init__(self, fres):
        self.fres         = fres
        self.header       = None
        self.headerOffset = None
        self.attrs        = []
        self.buffers      = []
        self.vtx_attrib_dict = None


    def __str__(self):
        return "<FVTX(@%s) at 0x%x>" %(
            '?' if self.headerOffset is None else hex(self.headerOffset),
            id(self),
        )


    def dump(self):
        """Dump to string for debug."""
        res = []
        res.append('  FVTX index %2d: %3d attrs, %3d buffers, %4d vtxs; Skin weight influence: %d' % (
            self.header['index'],
            self.header['num_attrs'],
            self.header['num_bufs'],
            self.header['num_vtxs'],
            self.header['skin_weight_influence'],
        ))
        res.append('  Unk04: 0x%08X 0x%08X 0x%08X' %
            self.header['unk04'],
        )
        res.append('  Unk10: 0x%08X 0x%08X 0x%08X' % (
            self.header['unk10'], self.header['unk18'],
            self.header['unk20'],
        ))
        res.append('  Attrib Array: 0x%06X, Dict:   0x%06X' % (
            self.header['vtx_attrib_array_offs'],
            self.header['vtx_attrib_dict_offs'],
        ))
        res.append("  Attrib Dict: "+
            self.vtx_attrib_dict.dump().replace('\n', '\n  '))

        if len(self.attrs) > 0:
            res.append('  Attribute Dump:')
            res.append('    \x1B[4m#  │Idx│BufOfs│Format       │Unk04   │Attr Name\x1B[0m')
            for i, attr in enumerate(self.attrs):
                res.append('    %3d│%s' % (i, attr.dump()))

        res.append('  Buffer Array: 0x%06X, Data:   0x%06X' % (
            self.header['vtx_buf_array_offs'],
            self.header['vtx_buf_offs'],
        ))
        res.append('  BufSiz Array: 0x%06X, Stride: 0x%06X' % (
            self.header['vtx_bufsize_offs'],
            self.header['vtx_stridesize_offs'],
        ))

        if len(self.buffers) > 0:
            res.append('    \x1B[4mOffset│Size│Strd│Buffer data\x1B[0m')
            for buf in self.buffers:
                res.append('    ' + buf.dump())
        return '\n'.join(res).replace('\n', '\n  ')


    def readFromFRES(self, offset=None):
        """Read this object from given file."""
        if offset is None: offset = self.fres.file.tell()
        print("Reading FVTX from 0x%06X" % offset)
        self.headerOffset = offset
        self.header = self.fres.read(Header(), offset)

        self._readDicts()
        self._readBuffers()
        self._readAttrs()
        self._readVtxs()
        return self


    def _readDicts(self):
        """Read the dicts belonging to this FVTX."""
        self.vtx_attrib_dict = Dict(self.fres)
        self.vtx_attrib_dict.readFromFRES(
            self.header['vtx_attrib_dict_offs'])


    def _readBuffers(self):
        """Read the attribute data buffers."""
        dataOffs = self.fres.rlt.dataStart + self.header['vtx_buf_offs']
        bufSize    = self.header['vtx_bufsize_offs']
        strideSize = self.header['vtx_stridesize_offs']

        self.buffers = []
        file = self.fres.file
        for i in range(self.header['num_bufs']):
            n      = i*0x10
            size   = self.fres.read('I', bufSize+n)
            stride = self.fres.read('I', strideSize+n)
            buf    = Buffer(self.fres, size, stride, dataOffs)
            self.buffers.append(buf)
            dataOffs += buf.size


    def _readAttrs(self):
        """Read the attribute definitions."""
        self.attrs = []
        self.attrsByName = {}
        offs = self.header['vtx_attrib_array_offs']
        for i in range(self.header['num_attrs']):
            attr = Attribute(self).readFromFRES(offs)
            self.attrs.append(attr)
            self.attrsByName[attr.name] = attr
            offs += AttrStruct.size


    def _readVtxs(self):
        """Read the vertices from the buffers."""
        self.vtxs = []
        for i in range(self.header['num_vtxs']):
            vtx = Vertex()
            for attr in self.attrs: # get the data for each attribute
                buf  = self.buffers[attr.buf_idx]
                offs = attr.buf_offs + (i * buf.stride)
                fmt  = attr.format

                # get the conversion function if any
                func = None
                if type(fmt) is dict:
                    func = fmt.get('func', None)
                    fmt  = fmt['fmt']

                # get the data
                data = struct.unpack_from(fmt, buf.data, offs)
                if func: data = func(data)
                vtx.setAttr(attr, data)

            self.vtxs.append(vtx)
