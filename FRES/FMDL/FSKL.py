from io_scene_bfres.BinaryStruct import BinaryStruct, BinaryObject
from io_scene_bfres.BinaryStruct.Padding import Padding
from io_scene_bfres.BinaryStruct.StringOffset import StringOffset
from io_scene_bfres.BinaryStruct.Switch import Offset32, Offset64, String
from io_scene_bfres.BinaryStruct.Flags import Flags
from io_scene_bfres.BinaryFile import BinaryFile
from io_scene_bfres.FRES.FresObject import FresObject
from io_scene_bfres.FRES.Dict import Dict
from .Bone import Bone
import struct
import math


class Header(BinaryStruct):
    """FSKL header."""
    magic  = b'FSKL'
    fields = (
        ('4s', 'magic'),
        ('I',  'size'),
        ('I',  'size2'),
        Padding(4),
        Offset64('bone_idx_group_offs'),
        Offset64('bone_array_offs'),
        Offset64('smooth_idx_offs'),
        Offset64('smooth_mtx_offs'),
        Offset64('unk30'),
        Flags('flags', {
            #'SCALE_NONE': 0x00000000, # no scaling
            'SCALE_STD':  0x00000100, # standard scaling
            'SCALE_MAYA': 0x00000200, # Respects Maya's segment scale
                # compensation which offsets child bones rather than
                # scaling them with the parent.
            'SCALE_SOFTIMAGE': 0x00000300, # Respects the scaling method
                # of Softimage.
            'EULER': 0x00001000, # euler rotn, not quaternion
        }),
        ('H',  'num_bones'),
        ('H',  'num_smooth_idxs'),
        ('H',  'num_rigid_idxs'),
        ('H',  'num_extra'),
        ('I',  'unk44'),
    )
    size = 0x48


class FSKL(FresObject):
    """A skeleton in an FRES."""
    Header = Header

    def __init__(self, fres):
        self.fres         = fres
        self.header       = None
        self.headerOffset = None


    def __str__(self):
        return "<FSKL(@%s) at 0x%x>" %(
            '?' if self.headerOffset is None else hex(self.headerOffset),
            id(self),
        )


    def dump(self):
        """Dump to string for debug."""
        res  = []
        res.append("  Size: 0x%08X / 0x%08X" % (
            self.header['size'],
            self.header['size2']))
        res.append("Bone Idx Group Offs: 0x%08X" %
            self.header['bone_idx_group_offs'])
        res.append("Bone Array Offs: 0x%08X" %
            self.header['bone_array_offs'])
        res.append("Smooth Idx Offs: 0x%08X" %
            self.header['smooth_idx_offs'])
        res.append("Smooth Mtx Offs: 0x%08X" %
            self.header['smooth_mtx_offs'])
        res.append("Unk30: 0x%08X" % self.header['unk30'])
        res.append("Flags: %s" % str(self.header['flags']))
        res.append("Bones: %3d" % self.header['num_bones'])
        res.append("Smooth Idxs: %3d" % self.header['num_smooth_idxs'])
        res.append("Rigid Idxs: %3d" % self.header['num_rigid_idxs'])
        res.append("Extras: %3d" % self.header['num_extra'])
        res.append("Unk44:  0x%08X" % self.header['unk44'])
        for bone in self.bones:
            res.append(bone.dump())
        return '\n'.join(res).replace('\n', '\n  ')


    def readFromFRES(self, offset=None):
        """Read this object from given file."""
        if offset is None: offset = self.fres.file.tell()
        print("Reading FSKL from 0x%06X" % offset)
        self.headerOffset = offset
        self.header = self.fres.read(Header(), offset)

        self._readSmoothIdxs()
        self._readSmoothMtxs()
        self._readBones()

        return self


    def _readSmoothIdxs(self):
        """Read smooth matrix indices."""
        self.smooth_idxs = self.fres.read('h',
            pos   = self.header['smooth_idx_offs'],
            count = self.header['num_smooth_idxs'])


    def _readSmoothMtxs(self):
        """Read smooth matrices."""
        self.smooth_mtxs = []
        for i in range(max(self.smooth_idxs)):
            # read the matrix
            mtx = self.fres.read('3f', count = 4,
                pos = self.header['smooth_mtx_offs'] + (i*16*3))

            # warn about invalid values
            for y in range(4):
                for x in range(3):
                    n = mtx[y][x]
                    if math.isnan(n) or math.isinf(n):
                        print("FRES: Skeleton smooth mtx %d element [%d,%d] is %s" % (
                            i, x, y, n))

            # replace all invalid values with zeros
            flt = lambda e: \
                0 if (math.isnan(e) or math.isinf(e)) else e
            mtx = list(map(lambda row: list(map(flt, row)), mtx))

            self.smooth_mtxs.append(mtx)


    def _readBones(self):
        """Read the bones."""
        self.bones = []
        self.bonesByName = {}
        self.boneIdxGroups = []
        offs = self.header['bone_array_offs']

        # read the bones
        for i in range(self.header['num_bones']):
            b = Bone(self.fres).readFromFRES(offs)
            self.bones.append(b)
            if b.name in self.bonesByName:
                print("FRES: Duplicate bone name '%s'" % b.name)
                self.bonesByName[b.name] = b
            offs += Bone._struct.size

        # set parents
        for bone in self.bones:
            bone.fskl = self
            if bone.parent_idx >= len(self.bones):
                print("FRES: Bone %s has invalid parent_idx %d (max is %d)" % (
                    bone.name, bone.parent_idx, len(self.bones)))
                bone.parent = None
            elif bone.parent_idx >= 0:
                bone.parent = self.bones[bone.parent_idx]
            else:
                bone.parent = None

        self.boneIdxGroups = Dict(self.fres).readFromFRES(
            self.header['bone_idx_group_offs'])