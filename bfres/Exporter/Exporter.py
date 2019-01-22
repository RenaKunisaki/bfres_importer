import logging; log = logging.getLogger(__name__)
import bmesh
import bpy
import bpy_extras
import os
import os.path
import tempfile
import shutil
import struct
import math
from bfres.Exceptions import UnsupportedFileTypeError
from bfres.BinaryFile import BinaryFile
from bfres import YAZ0, FRES, BNTX
#from .ModelImporter import ModelImporter
#from .TextureImporter import TextureImporter


class Exporter:
    def __init__(self, operator, context):
        self.operator = operator
        self.context  = context

        # Keep a link to the add-on preferences.
        #self.addon_prefs = #context.user_preferences.addons[__package__].preferences


    def run(self, path):
        """Perform the export."""
        self.wm   = bpy.context.window_manager
        self.path = path
        log.info("EXPORT GOES HERE")
        return {'FINISHED'}
