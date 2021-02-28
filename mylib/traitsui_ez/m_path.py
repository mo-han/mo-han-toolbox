#!/usr/bin/env python3
# encoding=utf8
from pathlib import Path as PrimePath

from .i1_traits_only import *


class EasyPath:
    """Simple wrap class of `pathlib.Path`"""

    def __init__(self, *args, **kwargs):
        self.path = PrimePath(*args, **kwargs)

    def __str__(self):
        return f'{self.__class__.__name__}({repr(self.full)})'

    @property
    def full(self):
        return str(self.path)

    @full.setter
    def full(self, value):
        if isinstance(value, str):
            self.path = PrimePath(value)
        elif isinstance(value, (tuple, list)):
            self.path = PrimePath(*value)
        else:
            raise TypeError(value, (str, tuple, list))

    @property
    def dirname(self):
        return str(self.path.parent)

    @dirname.setter
    def dirname(self, value):
        if isinstance(value, str):
            new_parent = value
        elif isinstance(value, (tuple, list)):
            new_parent = PrimePath(*value)
        else:
            raise TypeError(value, (str, tuple, list))
        self.path = PrimePath(new_parent, self.path.name)

    @property
    def basename(self):
        return self.path.name

    @basename.setter
    def basename(self, value):
        self.path = self.path.with_name(value)

    @property
    def stem(self):
        return self.path.stem

    @stem.setter
    def stem(self, value):
        self.path = self.path.with_name(f'{value}{self.path.suffix}')

    @property
    def extension(self):
        return self.path.suffix

    @extension.setter
    def extension(self, value):
        try:
            self.path = self.path.with_suffix(value)
        except ValueError:
            pass


class Path(HasTraits):
    full = tn.full = Str
    dirname = tn.dirname = Str
    basename = tn.basename = Str
    stem = tn.stem = Str
    extension = tn.extension = Str

    nl = [tn.full, tn.dirname, tn.basename, tn.stem, tn.extension]

    def __init__(self, *args, **kwargs):
        super(Path, self).__init__(**kwargs)
        self.path = EasyPath(*args)
        self._update()

    def _update(self):
        for name in self.nl:
            name: str
            setattr(self, name, getattr(self.path, name))

    @observe(nl)
    def _change(self, e: ob_evt.TraitChangeEvent):
        setattr(self.path, e.name, e.new)
        self._update()
