#!/usr/bin/env python3
import builtins
import os as _os
from io import *

from ezpykit.stdlib import typing as T


class SliceFileIO(FileIO):
    """slice data in FileIO object"""

    def __init__(self, file, mode='rb', *args, **kwargs):
        """refer to doc string of io.FileIO"""
        super().__init__(file, mode=mode, *args, **kwargs)
        try:
            self._size = _os.path.getsize(file)
        except TypeError:
            self._size = _os.path.getsize(self.name)

    def __len__(self):
        return self._size

    @property
    def size(self):
        return self._size

    def __getitem__(self, key: int or slice):
        orig_pos = self.tell()
        if isinstance(key, int):
            if key < 0:
                key = self.size + key
            self.seek(key)
            r = self.read(1)
        elif isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if not start:
                start = 0
            elif start < 0:
                start = self.size + start
            if not stop:
                stop = self.size
            elif stop < 0:
                stop = self.size + stop
            size = stop - start
            if size <= 0:
                r = b''
            elif not step or step == 1:
                self.seek(start)
                r = self.read(size)
            else:
                r = self.read(size)[::step]
        else:
            raise TypeError(key, (int, slice), type(key))
        self.seek(orig_pos)
        return r

    def __setitem__(self, key: int or slice, value: bytes):
        orig_pos = self.tell()
        value_len = len(value)

        if isinstance(key, int):
            if value_len != 1:
                raise NotImplementedError("overflow write")
            if key < 0:
                key = self.size + key
            self.seek(key)
            self.write(value)
        elif isinstance(key, slice):
            if key.step not in (None, 1):
                raise NotImplementedError('non-sequential write')
            start, stop = key.start, key.stop
            if not start and not stop:
                self.truncate(value_len)
                start = stop = 0
                slice_len = value_len
            else:
                start = start or 0
                if start < 0:
                    start += self._size
                stop = stop or 0
                if stop < 0:
                    stop += self._size
                slice_len = stop - start
            if value_len <= slice_len:
                self.seek(start)
                self.write(value)
                self._size = max(self.size, start + value_len)
            else:
                raise NotImplementedError('overflow write')
        else:
            raise TypeError(key, (int, slice), type(key))
        self.seek(orig_pos)


class IOKit:
    @staticmethod
    def read_exit(x, *args, **kwargs):
        with x:
            return x.read(*args, **kwargs)

    @staticmethod
    def write_exit(x, *args, **kwargs):
        with x:
            return x.write(*args, **kwargs)


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

    @classmethod
    def get(cls, vfname, mode: str, **kwargs):
        if any([i in mode for i in 'ax+']):
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
            if has_bin == want_bin:
                return vf
            elif want_bin:
                return cls.new(vfname, binary=True, value=vf.getvalue().encode(kwargs.get('encoding') or 'utf-8'))
            else:
                return cls.new(vfname, binary=False, value=vf.getvalue().decode(kwargs.get('encoding') or 'utf-8'))
        else:
            return cls.new(vfname, binary=want_bin)

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
        return open(
            file, mode=mode, **kwargs)


def replace_open_support_vitual_file_io():
    open_virtual_file_io.replace = builtins.open
    builtins.open = open_virtual_file_io


def restore_open():
    builtins.open = open_virtual_file_io.replace
