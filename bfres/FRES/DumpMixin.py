import logging; log = logging.getLogger(__name__)

class DumpMixin:
    """Mixin class for dump methods of FRES."""
    def dump(self):
        """Dump to string for debug."""
        res = []
        self._dumpHeader     (res)
        self._dumpObjects    (res)
        self._dumpBufMemPool (res)
        self._dumpStringTable(res)
        self._dumpRLT        (res)
        self._dumpModels     (res)
        self._dumpAnimations (res)
        self._dumpBuffers    (res)
        self._dumpEmbeds     (res)
        return '\n'.join(res).replace('\n', '\n  ')


    def _dumpHeader(self, res):
        res.append('  FRES "%s"/"%s": Version: %d,%d, Size: 0x%06X, Endian: %s, Align: 0x%08X' % (
            self.name,
            self.header['name2'],
            self.header['version'][0],
            self.header['version'][1],
            self.header['file_size'],
            self.byteOrder,
            self.header['alignment'],
        ))
        res.append("  Unk24: 0x%08X UnkCA: 0x%04X 0x%04X 0x%04X" % (
            self.header['unk24'],
            self.header['unkCA'],
            self.header['unkCC'],
            self.header['unkCE'],
        ))


    def _dumpObjects(self, res):
        res.append("  \x1B[4mObject│Cnt │Offset  │DictOffs\x1B[0m")
        objs = ('fmdl', 'fska', 'fmaa', 'fvis', 'fshu', 'embed')
        for obj in objs:
            res.append("  %-6s│%04X│%08X│%08X" % (
                obj.upper(),
                self.header[obj+'_cnt'],
                self.header[obj+'_offset'],
                self.header[obj+'_dict_offset'],
            ))


    def _dumpBufMemPool(self, res):
        res.append("  Buffer│ ?? │%08X│%08X" % (
            self.header['buf_mem_pool'],
            self.header['buf_mem_pool_info'],
        ))


    def _dumpStringTable(self, res):
        res.append("  StrTab│N/A │%08X│N/A     │size=0x%06X num_strs=%d" % (
            self.header['str_tab_offset'],
            self.header['str_tab_size'],
            self.strtab.header['num_strs'],
        ))


    def _dumpRLT(self, res):
        res.append(self.rlt.dump())


    def _dumpModels(self, res):
        res.append("  Models: %d" % len(self.models))
        for i, model in enumerate(self.models):
            res.append(model.dump())


    def _dumpAnimations(self, res):
        res.append("  Animations: %d" % len(self.animations))
        for i, animation in enumerate(self.animations):
            res.append(animation.dump())


    def _dumpBuffers(self, res):
        res.append("  Buffers: %d" % len(self.buffers))
        for i, buffer in enumerate(self.buffers):
            res.append(buffer.dump())


    def _dumpEmbeds(self, res):
        res.append("  Embedded Files: %d" % len(self.embeds))
        if len(self.embeds) > 0:
            res.append('    \x1B[4mOffset│Size  │Name            |ASCII dump\x1B[0m')
            for i, embed in enumerate(self.embeds):
                res.append('    %06X│%06X│%-16s│%s' % (
                    embed.dataOffset,
                    embed.size, embed.name,
                    ''.join(map(
                        lambda b: \
                            chr(b) if (b >= 0x20 and b < 0x7F) \
                            else ('\\x%02X' % b),
                        embed.data[0:16]
                    )),
                ))
