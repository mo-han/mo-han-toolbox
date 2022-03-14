#!/usr/bin/env python3
import builtins
import io as _io
from io import StringIO, BytesIO
from contextlib import contextmanager


class VirtualFileIOBase:
    def close(self) -> None:
        self.value = self.getvalue()
        super(VirtualFileIOBase, self).close()

    def reopen(self, **kwargs):
        super(VirtualFileIOBase, self).__init__(self.value, **kwargs)
        delattr(self, 'value')

    def __init__(self, name, *args, **kwargs):
        super(VirtualFileIOBase, self).__init__(*args, **kwargs)
        self.name = name


class VirtualTextFileIO(VirtualFileIOBase, StringIO):
    pass


class VirtualBinaryFileIO(VirtualFileIOBase, BytesIO):
    pass


class VirtualFileManager:
    _files = {}

    @classmethod
    def new(cls, vfname: str, binary: bool, value=None):
        if binary:
            vf = VirtualBinaryFileIO(vfname)
        else:
            vf = VirtualTextFileIO(vfname)
        if value:
            vf.write(value)
            vf.seek(0)
        cls._files[vfname] = vf
        return vf

    @staticmethod
    def _post_process(vf, mode):
        if 'w' in mode:
            vf.truncate()
        elif 'a' in mode:
            vf.read()
        return vf

    @classmethod
    def get(cls, vfname, mode: str, **kwargs):
        if any([i in mode for i in 'x+']):
            raise NotImplementedError('mode', mode)
        want_bin = 'b' in mode
        if vfname in cls._files:
            vf = cls._files[vfname]
            if vf.closed:
                vf.reopen()
            if isinstance(vf, VirtualBinaryFileIO):
                has_bin = True
            elif isinstance(vf, VirtualTextFileIO):
                has_bin = False
            else:
                return cls.new(vfname, binary=want_bin)
            import locale
            encoding = kwargs.get('encoding') or locale.getpreferredencoding(False)
            if has_bin == want_bin:
                pass
            elif want_bin:
                vf = cls.new(vfname, binary=True, value=vf.getvalue().encode(encoding))
            else:
                vf = cls.new(vfname, binary=False, value=vf.getvalue().decode(encoding))
        else:
            vf = cls.new(vfname, binary=want_bin)
        return cls._post_process(vf, mode)

    @classmethod
    def set(cls, vfname, vfobj):
        if not isinstance(vfobj, VirtualFileIOBase):
            raise TypeError('invalid type as VirtualFileIO', type(vfobj))
        cls._files[vfname] = vfobj

    @classmethod
    def rm(cls, vfname):
        if vfname in cls._files:
            del cls._files[vfname]


def open_virtual_file_io(file, mode='r', **kwargs):
    if isinstance(file, str) and file.startswith('virtualfile:///'):
        return VirtualFileManager.get(file, mode, **kwargs)
    else:
        return _io.open(file, mode=mode, **kwargs)


def replace_open_support_virtualfileio():
    if not hasattr(open_virtual_file_io, 'replace'):
        open_virtual_file_io.replace = builtins.open
        builtins.open = open_virtual_file_io


def restore_open():
    builtins.open = open_virtual_file_io.replace
    delattr(open_virtual_file_io, 'replace')


@contextmanager
def ctx_open_virtualfileio():
    replace_open_support_virtualfileio()
    yield
    restore_open()