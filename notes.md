Fixed reading dicts with offset 0

# What works:
- Models
- Skeletons
- Textures/Materials

# What doesn't work (or isn't started yet):
- Assigning the correct UV map to each texture
    - Fox: u0 (#4) is Spm, Nrm, u1 (#5) is Alb
    - Even after manually assigning, the specular intensity is way too high
- Whatever is up with `npc_zelda_miko`
- Exporting
- Animations
- Doing something with the render/shader/material params, sampler list, other attributes
- BC1 decoding seems like the swizzle calculation is wrong

For bones: maybe "Smooth Mtx Idx" is really "group ID", to correspond with the vertex groups. So instead of adding 2, we use the bone that has the matching group ID.
Maybe "smooth matrix" is just someone's way of describing the whole vertex group/weight thing, and they don't really refer to a matrix?

How do we know which UV map goes to which texture?
The eye models only have u0
The main differences seem to be:
- Alb is SRGB, others are Unorm
- Spm is BC4 and only red channels
- Alb swizzle size is 0
what are the parent_offset and ptrs_offset?
I don't see anything in the main FRES that seems to relate to this.

                u1 (5)   |u1 (5)   |u0 (4)   |u0 (4)   |u0 (4)   |u0 (4)   |u0 (4)
Name:          |Fox_Alb.0|Fox_Alb.1|Eye_Alb  |Eye_Nrm  |Eye_Spm  |Fox_Nrm  |Fox_Spm
Length:        |02E8     |0BE0     |02D8     |02D0     |02D8     |02E8     |02E8
Flags:         |1        |1        |1        |1        |1        |1        |1
Dimensions:    |2        |2        |2        |2        |2        |2        |2
Tile Mode:     |0        |0        |0        |0        |0        |0        |0
Swiz Size:     |0        |0        |0        |2        |3        |2        |3  <-- all different
Mipmap Cnt:    |9        |9        |7        |6        |7        |9        |9
Multisample Cnt|1        |1        |1        |1        |1        |1        |1
Reserved 1A:   |0        |0        |0        |0        |0        |0        |0
Fmt Data Type: | 6 SRGB  | 6 SRGB  | 6 SRGB  | 1 Unorm | 1 Unorm | 1 UNorm | 1 UNorm  <-- interesting
Fmt Type:      |26 BC1   |26 BC1   |26 BC1   |26 BC1   |29 BC4   |26 BC1   |29 BC4
Access Flags:  |20       |20       |20       |20       |20       |20       |20
Width x Height:|256/  256|256/  256| 64/   64| 32/   32| 64/   64|256/  256|256/  256
Depth:         |  1      |  1      |  1      |  1      |  1      |  1      |  1
Array Cnt:     |  1      |  1      |  1      |  1      |  1      |  1      |  1
Block Height:  |  8      |  8      |  2      |  1      |  2      |  8      |  8
Unk38:         |0007 0001|0007 0001|0007 0001|0007 0001|0007 0001|0007 0001|0007 0001
Unk3C:         |0,0,0,0,0|0,0,0,0,0|0,0,0,0,0|0,0,0,0,0|0,0,0,0,0|0,0,0,0,0|0,0,0,0,0
Data Len:      |B400     |B400     |1400     |0C00     |1400     |B400     |B400
Alignment:     |0200     |0200     |0200     |0200     |0200     |0200     |0200
Channel Types: |RGBA     |RGBA     |RGBA     |RGBA     |RRRR     |RGBA     |RRRR
Texture Type:  |1        |1        |1        |1        |1        |1        |1
Parent Offs:   |20       |20       |20       |20       |20       |20       |20
Ptrs Offs:     |0578     |16B0     |0E30     |1108     |13D8     |0860     |0B48

interesting differences between FMATs
FMAT:                         0 Fox / Eye 1
uking_texture1_texcoord           1 / 0
uking_texture2_texcoord           1 / 0
uking_texture4_texcoord           0 / 6
uking_enable_proctexture4         0 / 1
uking_proctexture4_type           0 / 100
uking_proctexture4_param_A        0 / 104
uking_proctexture4_param_B        0 / 105
uking_texture5_texcoord           0 / 6
uking_enable_proctexture5         0 / 1
uking_proctexture5_type           0 / 100
uking_proctexture5_param_A        0 / 106
uking_proctexture5_param_B        0 / 107
uking_enable_texcoord1            1 / 0
uking_texcoord1_mapping           1 / 0
uking_enable_texcoord3            0 / 1
uking_texcoord3_mapping           0 / 20
uking_texcoord3_srt              -1 / 3
uking_texcoord_toon_spec_mapping  1 / 20
uking_material_behave             0 / 104
