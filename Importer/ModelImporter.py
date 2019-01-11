import bmesh
import bpy
import bpy_extras
import struct
from .MaterialImporter import MaterialImporter
from .SkeletonImporter import SkeletonImporter


class ModelImporter:
    """Mixin class for importing the geometric models."""

    def _importModel(self, fmdl):
        """Import specified model."""
        # create a parent if we don't have one.
        fmdl_obj = None
        if self.operator.parent_ob_name is None:
            fmdl_obj = bpy.data.objects.new(fmdl.name, None)
            self._add_object_to_group(fmdl_obj, fmdl.name)
            bpy.context.scene.objects.link(fmdl_obj)

        # import the skeleton
        self.fmdl = fmdl
        self.skelImp  = SkeletonImporter(self, fmdl)
        self.armature = self.skelImp.importSkeleton(fmdl.skeleton)

        # import the materials.
        self.matImp = MaterialImporter(self, fmdl)
        for i, fmat in enumerate(fmdl.fmats):
            print("FRES:   Importing material %3d / %3d..." % (
                i+1, len(fmdl.fmats)))
            self.matImp.importMaterial(fmat)

        # create the shapes.
        for i, fshp in enumerate(fmdl.fshps):
            print("FRES:   Importing shape %3d / %3d '%s'..." % (
                i+1, len(fmdl.fshps), fshp.name))
            self._importShape(fmdl, fshp, fmdl_obj)


    def _importShape(self, fmdl, fshp, parent):
        """Import FSHP.

        fmdl: FMDL to import from.
        fshp: FSHP to import.
        parent: Object to parent the LOD models to.
        """
        fvtx = fmdl.fvtxs[fshp.header['fvtx_idx']]
        for ilod, lod in enumerate(fshp.lods):
            print("FRES:     Importing LOD %3d / %3d..." % (
                ilod+1, len(fshp.lods)))

            idxs = lod.idx_buf
            # the game doesn't tell how many vertices each LOD has,
            # but we can usually rely on this.
            nVtxs = int(lod.header['idx_cnt'] / 3)

            # Create an object for this LOD
            lodName = "%s.%d" % (fshp.name, ilod)
            lod_obj = bpy.data.objects.new(lodName, None)

            # get the attribute buffer data
            attr_buffers = self._getAttrBuffers(lod, fvtx)
            p0 = attr_buffers['_p0']

            # create a mesh
            mesh = bmesh.new()
            self._addVerticesToMesh(mesh, p0)

            # add the faces
            # XXX don't assume triangles
            for i in range(0, len(idxs), 3):
                vs   = list(mesh.verts[j] for j in idxs[i:i+3])
                face = mesh.faces.new(vs)
                #face.smooth = True

            # Write the bmesh data back to a new mesh.
            fshp_mesh = bpy.data.meshes.new(lodName)
            mesh.to_mesh(fshp_mesh)
            mesh.free()
            mesh_obj = bpy.data.objects.new(fshp_mesh.name, fshp_mesh)
            mesh_obj.parent = parent
            mdata = mesh_obj.data
            bpy.context.scene.objects.link(mesh_obj)
            self._add_object_to_group(mesh_obj, fmdl.name)

            # Add material
            mat = fmdl.fmats[fshp.header['fmat_idx']]
            mdata.materials.append(bpy.data.materials[mat.name])

            # add UV map
            self._addUvMap(fvtx, mesh_obj, attr_buffers)

            # add vertex weights
            try:
                w0 = attr_buffers['_w0']
                self._makeVertexGroup(mesh_obj,
                    len(w0), attr_buffers)
            except KeyError:
                print("FRES: mesh '%s' has no weights" % lodName)

            # add armature
            mod = mesh_obj.modifiers.new(lodName, 'ARMATURE')
            mod.object = self.armature
            mod.use_bone_envelopes = False
            mod.use_vertex_groups  = True


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


    def _addUvMap(self, fvtx, mesh_obj, attr_buffers):
        """Add UV maps from `_u0`, `_u1`... attributes."""
        idx = 0
        while True:
            attr = '_u%d' % idx
            try: data = attr_buffers[attr]
            except KeyError: break

            vMax = fvtx.attrsByName[attr].format['max']
            mdata = mesh_obj.data
            mdata.uv_textures.new(attr)
            for i, poly in enumerate(mdata.polygons):
                for j, loopIdx in enumerate(poly.loop_indices):
                    loop = mdata.loops[loopIdx]
                    uvloop = mdata.uv_layers.active.data[loopIdx]
                    x, y = data[loop.vertex_index]
                    #print('meshloop: ', j, ' index: ',loopIdx, "vidx", loop.vertex_index, "coord", x, y)

                    uvloop.uv.x, uvloop.uv.y = x/vMax, y/vMax
            idx += 1


    def _makeVertexGroup(self, mesh_obj, nVtxs, attrs):
        """Make vertex group for mesh object from attributes."""
        # XXX move to SkeletonImporter?
        groups = {}
        try:
            w0 = attrs['_w0']
            i0 = attrs['_i0']
        except KeyError:
            print("FRES: mesh '%s' has no weights" % mesh_obj.name)
            return

        # create a vertex group for each bone
        # each bone affects the vertex group with the same
        # name as that bone, and these weights define how much.
        for bone in self.fmdl.skeleton.bones:
            grp = mesh_obj.vertex_groups.new(bone.name)
            groups[bone.smooth_mtx_idx] = grp

        # i0 specifies the bone smooth matrix group.
        # Look for a bone with the same group.
        for i in range(0, nVtxs):
            wgt = w0[i] # how much this bone affects this vertex
            idx = i0[i] # which bone index group
            for j, w in enumerate(wgt):
                if w > 0:
                    try:
                        groups[idx[j]].add([i], w/255.0, 'REPLACE')
                    except (KeyError, IndexError):
                        print("FRES: Bone group %d doesn't exist (referenced by weight of vtx %d, value %d)" % (
                            idx[j], i, w))


    def _getAttrBuffers(self, lod, fvtx):
        """Get attribute data for given LOD.

        lod:  LOD model.
        fvtx: FVTX whose buffers to use.

        Returns a dict of attribute name => [values].
        """
        attr_buffers = {}
        for attr in fvtx.attrs:
            attr_buffers[attr.name] = []

        for submesh in lod.submeshes:
            idxs = submesh['idxs']
            #log.debug("submesh idxs: %s", idxs)
            for idx in range(max(idxs)+1):
                for attr in fvtx.attrs:
                    fmt  = attr.format
                    func = fmt.get('func', None)
                    size = struct.calcsize(fmt['fmt'])
                    buf  = fvtx.buffers[attr.buf_idx]
                    offs = attr.buf_offs + (idx * buf.stride)
                    data = buf.data[offs : offs + size]
                    data = struct.unpack(fmt['fmt'], data)
                    if func: data = func(data)
                    attr_buffers[attr.name].append(data)

        #for name, buf in attr_buffers.items():
        #    log.debug("%s: %s", name, buf)
        return attr_buffers
