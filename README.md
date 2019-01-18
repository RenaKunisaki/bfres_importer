Nintendo BFRES importer (and eventually exporter) for Blender.

Imports models from games such as Breath of the Wild.

Currently only supports Switch formats (and probably not very well).

Based on https://github.com/Syroot/io_scene_bfres

Very much in development and may be full of bugs and rough corners.

# What works:
- Importing models, with their skeletons and textures, from `.bfres` and `.sbfres` files (at least `Animal_Fox` works)
    - Includes cases where textures are in a separate `.Tex.sbfres` file in the same directory
    - Textures are embedded in the `.blend` file
    - Each LOD (level of detail) model is imported as a separate object, which might look strange when all of them are visible.
    - Materials' render/shader/material parameters are stored as Blender custom properties on the material objects.
    - Text files in the FRES are embedded into the blend file.

# What's broken:
- Specular intensity is way too high (models are shinier than they should be)
- `npc_zelda_miko` is weird, needs investigation
- Decompressing is slow
    - Progress indicator sucks, but I don't think Blender provides any way to do a better one
- No way to turn off the generation of dump files
- `Animal_Bee`'s UV map is all wrong
- Importing fails if not in object mode

# What's not even started yet:
- Animations
- Exporting
- WiiU files

# Why another importer?
I wanted to convert to a common format such as Collada, which any 3D editor could then use, but Blender seems to have issues with every suitable format. ¯\\\_(ツ)\_/¯

Syroot's importer didn't work for me, and as far as I know, didn't support skeletons. Since I'd already made a convertor, it was easier to build an importer from that.
