import bmesh
import bpy
import bpy_extras
import struct
from .MaterialImporter import MaterialImporter
from .SkeletonImporter import SkeletonImporter
from io_scene_bfres.Exceptions import UnsupportedFormatError


class LodImporter:
    """Handles importing LOD models."""
    def __init__(self, parent):
        self.parent = parent


    def _importLod(self, fvtx, fmdl, fshp, lod, idx):
        """Import given LOD model."""
        self.fvtx   = fvtx
        self.fmdl   = fmdl
        self.fshp   = fshp
        self.lod    = lod
        self.lodIdx = idx
        self.attrBuffers = self._getAttrBuffers()

        # Create an object for this LOD
        self.lodName = "%s.%d" % (self.fshp.name, self.lodIdx)
        self.lodObj  = bpy.data.objects.new(self.lodName, None)
        self.meshObj = self._createMesh()

        self._addUvMap()
        self._addVertexWeights()
        self._addArmature()

        return self.meshObj


    def _getAttrBuffers(self):
        """Get attribute data for this LOD.

        Returns a dict of attribute name => [values].
        """
        attrBuffers = {}
        for attr in self.fvtx.attrs:
            attrBuffers[attr.name] = []

        for submesh in self.lod.submeshes:
            idxs = submesh['idxs']
            for idx in range(max(idxs)+1):
                for attr in self.fvtx.attrs:
                    fmt  = attr.format
                    func = fmt.get('func', None)
                    size = struct.calcsize(fmt['fmt'])
                    buf  = self.fvtx.buffers[attr.buf_idx]
                    offs = attr.buf_offs + (idx * buf.stride)
                    data = buf.data[offs : offs + size]
                    data = struct.unpack(fmt['fmt'], data)
                    if func: data = func(data)
                    attrBuffers[attr.name].append(data)

        #for name, data in attrBuffers.items():
        #    print("%s: %s" % (
        #        name, ' '.join(map(str, data[0:16]))
        #    ))
        return attrBuffers


    def _createMesh(self):
        p0   = self.attrBuffers['_p0']
        idxs = self.lod.idx_buf
        # the game doesn't tell how many vertices each LOD has,
        # but we can usually rely on this.
        nVtxs = int(self.lod.header['idx_cnt'] / 3)

        # create a mesh and add faces to it
        mesh = bmesh.new()
        self._addVerticesToMesh(mesh, p0)
        self._createFaces(idxs, mesh)

        # Write the bmesh data back to a new mesh.
        fshpMesh = bpy.data.meshes.new(self.lodName)
        mesh.to_mesh(fshpMesh)
        mesh.free()
        meshObj = bpy.data.objects.new(fshpMesh.name, fshpMesh)
        mdata   = meshObj.data
        bpy.context.scene.objects.link(meshObj)
        self.parent._add_object_to_group(meshObj, self.fmdl.name)

        # Add material
        mat = self.fmdl.fmats[self.fshp.header['fmat_idx']]
        mdata.materials.append(bpy.data.materials[mat.name])

        return meshObj


    def _createFaces(self, idxs, mesh):
        """Create the faces."""
        fmt = self.lod.prim_fmt
        meth = getattr(self, '_createFaces_'+fmt, None)
        if meth is None:
            print("FRES: Unsupported prim format:", fmt)
            raise UnsupportedFormatError(
                "Unsupported prim format: " + fmt)
        return meth(idxs, mesh)

    def _createFacesBasic(self, idxs, mesh, step, nVtxs):
        for i in range(0, len(idxs), step):
            vs   = list(mesh.verts[j] for j in idxs[i:i+nVtxs])
            face = mesh.faces.new(vs)
            face.smooth = self.parent.operator.smooth_faces

    def _createFaces_points(self, idxs, mesh):
        return self._createFacesBasic(idxs, mesh, 1, 1)

    def _createFaces_lines(self, idxs, mesh):
        return self._createFacesBasic(idxs, mesh, 2, 2)

    #def _createFaces_line_strip(self, idxs, mesh):
    #    return self._createFacesBasic(idxs, mesh, 1, 2)

    #def _createFaces_line_loop(self, idxs, mesh):
    #    return self._createFacesBasic(idxs, mesh, 1, 2)

    def _createFaces_triangles(self, idxs, mesh):
        return self._createFacesBasic(idxs, mesh, 3, 3)

    def _createFaces_triangle_strip(self, idxs, mesh):
        return self._createFacesBasic(idxs, mesh, 1, 3)

    def _createFaces_quads(self, idxs, mesh):
        return self._createFacesBasic(idxs, mesh, 4, 4)

    # XXX this seems wrong
    _createFaces_line_strip = _createFaces_triangles
    _createFaces_line_loop  = _createFaces_triangles


    def _addVerticesToMesh(self, mesh, vtxs):
        """Add vertices (from `_p0` attribute) to a `bmesh`."""
        for i in range(len(vtxs)):
            if len(vtxs[i]) == 4:
                x, y, z, w = vtxs[i]
            else:
                x, y, z = vtxs[i]
                w = 1
            if w != 1:
                # Blender doesn't support the W coord,
                # but it's never used anyway.
                print("FRES: FSHP vertex W is", w)
            mesh.verts.new((x, -z, y))
        mesh.verts.ensure_lookup_table()
        mesh.verts.index_update()


    def _addUvMap(self):
        """Add UV maps from `_u0`, `_u1`... attributes."""
        idx = 0
        while True:
            attr = '_u%d' % idx
            try: data = self.attrBuffers[attr]
            except KeyError: break

            vMax  = self.fvtx.attrsByName[attr].format.get('max', 1)
            mdata = self.meshObj.data
            mdata.uv_textures.new(attr)
            for i, poly in enumerate(mdata.polygons):
                for j, loopIdx in enumerate(poly.loop_indices):
                    loop = mdata.loops[loopIdx]
                    uvloop = mdata.uv_layers.active.data[loopIdx]
                    x, y = data[loop.vertex_index]
                    uvloop.uv.x, uvloop.uv.y = x/vMax, y/vMax
            idx += 1


    def _addVertexWeights(self):
        """Add vertex weights (`_w0` attribute) to mesh."""
        try:
            self._makeVertexGroup()
        except KeyError:
            print("FRES: mesh '%s' has no weights" % self.lodName)


    def _addArmature(self):
        """Add armature to mesh."""
        mod = self.meshObj.modifiers.new(self.lodName, 'ARMATURE')
        mod.object = self.parent.armature
        mod.use_bone_envelopes = False
        mod.use_vertex_groups  = True
        return mod


    def _makeVertexGroup(self):
        """Make vertex group for mesh object from attributes."""
        # XXX move to SkeletonImporter?
        groups = {}
        try:
            w0 = self.attrBuffers['_w0']
            i0 = self.attrBuffers['_i0']
        except KeyError:
            print("FRES: mesh '%s' has no weights" % self.meshObj.name)
            return

        # create a vertex group for each bone
        # each bone affects the vertex group with the same
        # name as that bone, and these weights define how much.
        for bone in self.fmdl.skeleton.bones:
            grp = self.meshObj.vertex_groups.new(bone.name)
            groups[bone.smooth_mtx_idx] = grp

        # i0 specifies the bone smooth matrix group.
        # Look for a bone with the same group.
        for i in range(0, len(w0)):
            wgt = w0[i] # how much this bone affects this vertex
            idx = i0[i] # which bone index group
            for j, w in enumerate(wgt):
                if w > 0:
                    try:
                        groups[idx[j]].add([i], w/255.0, 'REPLACE')
                    except (KeyError, IndexError):
                        print("FRES: Bone group %d doesn't exist (referenced by weight of vtx %d, value %d)" % (
                            idx[j], i, w))
