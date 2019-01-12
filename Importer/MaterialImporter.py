import bmesh
import bpy
import bpy_extras
import struct

class MaterialImporter:
    """Imports material from FMDL."""

    def __init__(self, parent, fmdl):
        self.fmdl     = fmdl
        self.operator = parent.operator
        self.context  = parent.context


    def importMaterial(self, fmat):
        """Import specified material."""
        mat = bpy.data.materials.new(fmat.name)
        mat.specular_intensity = 0  # Do not make materials without specular map shine exaggeratedly.
        mat.use_transparency = True
        mat.alpha = 1
        mat.specular_alpha = 1

        for i, tex in enumerate(fmat.textures):
            print("FRES:     Importing Texture %3d / %3d '%s'..." % (
                i+1, len(fmat.textures), tex['name']))
            texObj = self._importTexture(fmat, tex)

            # Add texture slot
            # XXX use tex['slot'] if it's ever not -1
            name = tex['name'].split('.')
            if len(name) > 1:
                name, idx = name
            else:
                name = name[0]
                idx  = 0

            mtex                       = mat.texture_slots.add()
            mtex.texture               = texObj
            mtex.texture_coords        = 'UV'
            mtex.emission_color_factor = 0.5
            #mtex.use_map_density       = True
            mtex.mapping               = 'FLAT'

            if name.endswith('_Nrm'): # normal map
                mtex.use_map_color_diffuse  = False
                mtex.use_map_normal         = True

            elif name.endswith('_Spm'): # specular map
                mtex.use_map_color_diffuse  = False
                mtex.use_map_specular       = True

            elif name.endswith('_Alb'): # albedo (regular texture)
                mtex.use_map_color_diffuse  = True
                mtex.use_map_color_emission = True
                mtex.use_map_alpha          = True

            else:
                print("FRES: Don't know what to do with texture:", name)

            param = "uking_texture%d_texcoord" % i
            param = fmat.materialParams.get(param, None)
            if param:
                mat.texture_slots[0].uv_layer = "_u"+param
            else:
                print("FRES: No texcoord attribute for texture %d" % i)

        return mat


    def _importTexture(self, fmat, tex):
        """Import specified texture to specified material."""
        # do we use the texid anymore?
        texid = tex['name'].replace('.', '_') # XXX ensure unique
        texture = bpy.data.textures.new(texid, 'IMAGE')
        texture.image = bpy.data.images[tex['name']]
        return texture
