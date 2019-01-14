import bmesh
import bpy
import bpy_extras
import os
import tempfile
import struct
import math
from io_scene_bfres.Exceptions import UnsupportedFileTypeError
from io_scene_bfres.BinaryFile import BinaryFile
from io_scene_bfres import YAZ0, FRES, BNTX
from .ModelImporter import ModelImporter
from .TextureImporter import TextureImporter


class Importer(ModelImporter):
    def __init__(self, operator, context):
        self.operator = operator
        self.context  = context

        # Keep a link to the add-on preferences.
        #self.addon_prefs = #context.user_preferences.addons[__package__].preferences


    @staticmethod
    def _add_object_to_group(ob, group_name):
        # Get or create the required group.
        group = bpy.data.groups.get(group_name,
            bpy.data.groups.new(group_name))

        # Link the provided object to it.
        if ob.name not in group.objects:
            group.objects.link(ob)
        return group


    def run(self, path):
        """Perform the import."""
        self.wm   = bpy.context.window_manager
        self.path = path
        return self.unpackFile(path)


    def unpackFile(self, file):
        """Try to unpack the given file.

        file: A file object, or a path to a file.

        If the file format is recognized, will try to unpack it.
        If the file is compressed, will first decompress it and
        then try to unpack the result.
        Raises UnsupportedFileTypeError if the file format isn't
        recognized.
        """
        if type(file) is str: # a path
            file = BinaryFile(file)
        self.file = file

        # read magic from header
        file.seek(0) # rewind
        magic = file.read(4)
        file.seek(0) # rewind

        if magic in (b'Yaz0', b'Yaz1'): # compressed
            r = self.decompressFile(file)
            return self.unpackFile(r)

        elif magic == b'FRES':
            return self._importFres(file)

        elif magic == b'BNTX':
            return self._importBntx(file)

        else:
            raise UnsupportedFileTypeError(magic)


    def decompressFile(self, file):
        """Decompress given file.

        Returns a temporary file.
        """
        print("FRES: Decompressing input file...")
        result = tempfile.TemporaryFile()

        # make progress callback to update UI
        progress = 0
        def progressCallback(cur, total):
            nonlocal progress
            pct = math.floor((cur / total) * 100)
            if pct - progress >= 1:
                self.wm.progress_update(pct)
                progress = pct
        self.wm.progress_begin(0, 100)

        # decompress the file
        decoder = YAZ0.Decoder(file, progressCallback)
        for data in decoder.bytes():
            result.write(data)
        self.wm.progress_end()

        result.seek(0)
        return BinaryFile(result)


    def _importFres(self, file):
        """Import FRES file."""
        self.fres = FRES.FRES(file)
        self.fres.decode()

        with open('./fres-%s-dump.txt' % self.fres.name, 'w') as f:
            f.write(self.fres.dump())
        #print("FRES contents:\n" + self.fres.dump())

        # decode embedded files
        for i, file in enumerate(self.fres.embeds):
            try:
                self.unpackFile(file.toTempFile())
            except UnsupportedFileTypeError as ex:
                print("FRES: Embedded file '%s' is of unsupported type '%s'" % (
                    file.name, ex.magic))

        # import the models.
        for i, model in enumerate(self.fres.models):
            print("FRES: Importing model    %3d / %3d..." % (
                i+1, len(self.fres.models)))
            self._importModel(model)

        return {'FINISHED'}


    def _importBntx(self, file):
        """Import BNTX file."""
        self.bntx = BNTX.BNTX(file)
        self.bntx.decode()
        with open('./fres-%s-bntx-dump.txt' % self.bntx.name, 'w') as f:
            f.write(self.bntx.dump())

        imp = TextureImporter(self)
        imp.importTextures(self.bntx)

        return {'FINISHED'}
