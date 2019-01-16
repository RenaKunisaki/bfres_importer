For bones: maybe "Smooth Mtx Idx" is really "group ID", to correspond with the vertex groups. So instead of adding 2, we use the bone that has the matching group ID.
Maybe "smooth matrix" is just someone's way of describing the whole vertex group/weight thing, and they don't really refer to a matrix?

bee u0: (22464, 10104) (1370, 2112) (55092, 53581) (9476, 26471) (33738, 19565) (12310, 45140) (57864, 33886) (4604, 30817) (27794, 12662) (40550, 639) (52128, 34650) (59632, 52558) (14784, 16492) (55444, 60747) (22464, 55672) (33737, 46189)

fox u0: (51, 104) (6, 234) (127, 213) (208, 132) (130, 60) (247, 21) (51, 104) (127, 213) (6, 234) (208, 132) (130, 60) (247, 21) (51, 104) (6, 234) (127, 213) (208, 132)

Link:     5557 vtxs,  7104 faces,   7104 tris
Renamon:  5493 vtxs,  8357 faces,  10524 tris

Fox textures
Property        | Fox_Alb.0  | Fox_Eye_Alb | Differences
----------------|------------|-------------|------------
Length          | 0x0002E8   | 0x0002D8    | *
Length 2        | 0x0002E8   | 0x0002D8    | *
Flags           | 0x01       | 0x01        |
Dimensions      | 0x02       | 0x02        |
Tile Mode       | 0x0000     | 0x0000      |
Swiz Size       | 0x0000     | 0x0000      |
Mipmap Cnt      | 0x0009     | 0x0007      | *
Multisample Cnt | 0x0001     | 0x0001      |
Reserved 1A     | 0x0000     | 0x0000      |
Fmt Data Type   | 6 SRGB     | 6 SRGB      |
Fmt Type        | 26 BC1     | 26 BC1      |
Access Flags    | 0x00000020 | 0x00000020  |
Width x Height  | 256/  256  |  64/   64   | *
Depth           | 1          | 1           |
Array Cnt       | 1          | 1           |
Block Height    | 8          | 2           | *
Unk38           | 0007 0001  | 0007 0001   |
Unk3C           | 0,0,0,0,0  | 0,0,0,0,0   |
Data Len        | 0x0000B400 | 0x00001400  | *
Alignment       | 0x00000200 | 0x00000200  |
Channel Types   | RGBA       | RGBA        |
Texture Type    | 0x00000001 | 0x00000001  |
Parent Offs     | 0x00000020 | 0x00000020  |
Ptrs Offs       | 0x00000578 | 0x00000E30  | *
