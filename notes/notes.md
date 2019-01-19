For bones: maybe "Smooth Mtx Idx" is really "group ID", to correspond with the vertex groups. So instead of adding 2, we use the bone that has the matching group ID.
Maybe "smooth matrix" is just someone's way of describing the whole vertex group/weight thing, and they don't really refer to a matrix?

bee u0: (22464, 10104) (1370, 2112) (55092, 53581) (9476, 26471) (33738, 19565) (12310, 45140) (57864, 33886) (4604, 30817) (27794, 12662) (40550, 639) (52128, 34650) (59632, 52558) (14784, 16492) (55444, 60747) (22464, 55672) (33737, 46189)

fox u0: (51, 104) (6, 234) (127, 213) (208, 132) (130, 60) (247, 21) (51, 104) (127, 213) (6, 234) (208, 132) (130, 60) (247, 21) (51, 104) (6, 234) (127, 213) (208, 132)

    |Vtxs|Faces|Tris|Bones|Texs
----|----|-----|----|-----|----
Link|5557| 7104|7104|  115|  35
Rena|5033| 7797|9612|  440|   3

I assume the bones need to have the same names...
may not matter if there are additional bones
same for textures

so the actual process would be:
- rename bones, vtx groups, textures to match original model
- replace bones, vertices, textures in the file
    - attributes p0, u0, i0?

poach, pod are things on the belt
Pod_A is shield attach?
each bone has a corresponding group
actually the rigs might be too different,
may need to re-rig the new model manually...

as for exporting to bfres, we can probably do that, but there are many unknown parameters we would need to generate:
- shader params
- render params
- material params
- relocation table
- all unknown fields
without generating most of these correctly, games probably won't accept the file.
we can cheat a bit and use the properties from a previously imported file.
