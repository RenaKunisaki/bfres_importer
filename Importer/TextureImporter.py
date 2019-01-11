import bmesh
import bpy
import bpy_extras
import struct

class TextureImporter:
    """Imports texture images from BNTX archive."""

    def __init__(self, parent):
        self.operator = parent.operator
        self.context  = parent.context


    def importTextures(self, bntx):
        """Import textures from BNTX."""
        images = {}
        for i, tex in enumerate(bntx.textures):
            print("FRES: Importing texture %3d/%3d '%s'..." % (
                i+1, len(bntx.textures), tex.name))

            image = bpy.data.images.new(tex.name,
                width=tex.width, height=tex.height)
            image.use_alpha = True

            pixels = [None] * tex.width * tex.height
            offs   = 0
            for y in range(tex.height):
                for x in range(tex.width):
                    b, g, r, a = tex.pixels[offs:offs+4]
                    pixels[(y*tex.width)+x] = (
                        r / 255.0,
                        g / 255.0,
                        b / 255.0,
                        a / 255.0,
                    )
                    offs += 4
            # flatten list
            pixels = [chan for px in pixels for chan in px]
            image.pixels = pixels

            # save to file
            #image.filepath_raw = "/home/rena/projects/botw/tools/test-output/" + tex.name + ".png"
            #image.file_format = 'PNG'
            #print("Saving image to", image.filepath_raw)
            #image.save()

            image.pack(True, bytes(tex.pixels), len(tex.pixels))
            images[tex.name] = image
        return images
