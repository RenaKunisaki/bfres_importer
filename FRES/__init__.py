from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryFile import BinaryFile
from .RLT import RLT
from io_scene_bfres.Common import StringTable
from .Dict import Dict
from .EmbeddedFile import EmbeddedFile, Header as EmbeddedFileHeader
from .FMDL import FMDL, Header as FMDLHeader
from .DumpMixin import DumpMixin

# XXX WiiU header

class SwitchHeader(BinaryStruct):
    """Switch FRES header."""
    magic = b'FRES    ' # four spaces
    fields = (
        ('8s', 'magic'),
        ('<2H','version'),
        ('H',  'byte_order'), # FFFE=litle, FEFF=big
        ('H',  'header_len'), # always 0x0C

        String('name', lenprefix=None), # null-terminated filename
        Offset32('alignment'),
        # alignment might be U16, which would make it 0xD0,
        # which is the same size as this header.

        Offset32('rlt_offset'), # relocation table
        Offset32('file_size'), # size of this file

        String('name2'), # length-prefixed filename
        # name and name2 seem to always both be the filename
        # without extension, and in fact name points to the actual
        # string following the length prefix that name2 points to.

        Offset32('unk24'),

        Offset64('fmdl_offset'),
        Offset64('fmdl_dict_offset'),

        Offset64('fska_offset'),
        Offset64('fska_dict_offset'),

        Offset64('fmaa_offset'),
        Offset64('fmaa_dict_offset'),

        Offset64('fvis_offset'),
        Offset64('fvis_dict_offset'),

        Offset64('fshu_offset'),
        Offset64('fshu_dict_offset'),

        Offset64('fscn_offset'),
        Offset64('fscn_dict_offset'),

        Offset64('buf_mem_pool'),
        Offset64('buf_mem_pool_info'), # is this a dict?

        Offset64('embed_offset'),
        Offset64('embed_dict_offset'),

        Offset64('unkA8'),
        Offset64('str_tab_offset'),
        Offset32('str_tab_size'),

        ('H',    'fmdl_cnt'),
        ('H',    'fska_cnt'),
        ('H',    'fmaa_cnt'),
        ('H',    'fvis_cnt'),
        ('H',    'fshu_cnt'),
        ('H',    'fscn_cnt'),
        ('H',    'embed_cnt'),
        ('H',    'unkCA'),
        ('H',    'unkCC'),
        ('H',    'unkCE'),
    )
    size = 0xD0


class FRES(DumpMixin):
    """FRES file."""

    def __init__(self, file:BinaryFile):
        self.file       = file
        self.models     = [] # fmdl
        self.animations = [] # fska
        self.buffers    = [] # buffer data
        self.embeds     = [] # embedded files

        Header = SwitchHeader()
        self.header = Header.readFromFile(file)
        #print("FRES header:\n" + Header.dump(self.header))

        # extract some header info.
        self.name    = self.header['name']
        self.size    = self.header['file_size']
        self.version = self.header['version']

        if self.version != (3, 5):
            print("FRES: Unknown version 0x%04X 0x%04X" %
                self.version)

        if self.header['byte_order'] == 0xFFFE:
            self.byteOrder = 'little'
            self.byteOrderFmt = '<'
        elif self.header['byte_order'] == 0xFEFF:
            self.byteOrder = 'big'
            self.byteOrderFmt = '>'
        else:
            raise ValueError("Invalid byte order 0x%04X in FRES header" %
                self.header['byte_order'])


    def decode(self):
        """Decode objects from the file."""
        self.rlt = RLT(self).readFromFRES()
        #print("RLT data_start = 0x%08X" % self.rlt.dataStart)

        # str_tab_offset points to the first actual string, not
        # the header. (maybe it's actually the offset of some string,
        # which happens to be empty here?)
        offs = self.header['str_tab_offset'] - StringTable.Header.size
        self.strtab = StringTable().readFromFile(self, offs)

        self.embeds = self._readObjects(
            EmbeddedFile, 'embed', EmbeddedFileHeader.size)

        self.models = self._readObjects(FMDL, 'fmdl',
            FMDLHeader.size)
        # XXX fska, fmaa, fvis, fshu, fscn, buffer


    def _readObjects(self, typ, name, size):
        """Read array of objects from the file."""
        offs = self.header[name + '_offset']
        cnt  = self.header[name + '_cnt']
        dofs = self.header[name + '_dict_offset']
        objs = []
        print("FRES: Reading dict '%s' from 0x%X" % (name, dofs))
        if dofs == 0: return objs
        objDict = Dict(self).readFromFRES(dofs)
        for i in range(cnt):
            objName = objDict.root.left.name
            print('FRES: Reading %s #%2d @ %06X: "%s"' % (
                typ.__name__, i, offs, objName))
            obj = typ(self, objName).readFromFRES(offs)
            objs.append(obj)
            offs += size
        return objs


    def read(self, size:(int,str,BinaryStruct),
    pos:int=None, count:int=1,
    rel:bool=False):
        """Read data from file.

        fmt:   Number of bytes to read, or a `struct` format string,
               or a BinaryStruct.
        pos:   Position to seek to first. (optional)
        count: Number of items to read. If not 1, returns a list.

        Returns the data read.
        """
        if pos is None: pos = self.file.tell()
        if rel: pos += self.rlt.dataStart
        return self.file.read(pos=pos, fmt=size, count=count)


    def seek(self, pos, whence=0):
        """Seek the file."""
        return self.file.seek(pos, whence)


    def tell(self):
        """Report the current position of the file."""
        return self.file.tell()


    def readStr(self, offset, fmt='<H', encoding='shift-jis'):
        """Read string (prefixed with length) from given offset."""
        size = self.read(fmt, offset)
        data = self.read(size)
        if encoding is not None: data = data.decode(encoding)
        return data


    def readHex(self, cnt, offset):
        """Read hex string for debugging."""
        data = self.read(cnt, offset)
        hx   = map(lambda b: '%02X' % b, data)
        return ' '.join(hx)


    def readHexWords(self, cnt, offset):
        data = self.read('I', offset, cnt)
        hx   = map(lambda b: '%08X' % b, data)
        return ' '.join(hx)
