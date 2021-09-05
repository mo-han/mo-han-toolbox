#!/usr/bin/env python3
# encoding=utf8

from .i1_traits import *
from mylib.easy.extra.path_checker import is_path_valid


class PathSynthesizer:
    """Simple wrap class of `pathlib.Path`"""

    def __init__(self, *args, **kwargs):
        self.path = pathlib.Path(*args, **kwargs)

    def __str__(self):
        return f'{self.__class__.__name__}({repr(self.full)})'

    @property
    def full(self):
        return str(self.path)

    @full.setter
    def full(self, value):
        if isinstance(value, str):
            self.path = pathlib.Path(value)
        elif isinstance(value, (tuple, list)):
            self.path = pathlib.Path(*value)
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
            new_parent = pathlib.Path(*value)
        else:
            raise TypeError(value, (str, tuple, list))
        self.path = pathlib.Path(new_parent, self.path.name)

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


class PathComponent(String):
    def __init__(self, value: str = '', sync_to: PathSynthesizer = None, **metadata):
        super(PathComponent, self).__init__(value=value, **metadata)
        self.sync_path = sync_to

    def validate(self, obj, name, value):
        v = super(PathComponent, self).validate(obj, name, value)
        if is_path_valid(v):
            return v
        self.error(obj, name, value)

    @staticmethod
    def info():
        return 'a text string of valid path or path component'


class Path(HasTraits):
    full = tn.full = Str
    dirname = tn.dirname = Directory
    basename = tn.basename = Str
    stem = tn.stem = Str
    extension = tn.extension = Str

    nl = [tn.full, tn.dirname, tn.basename, tn.stem, tn.extension]

    def __init__(self, *path_parts, **kwargs):
        super(Path, self).__init__(**kwargs)
        self.path = PathSynthesizer(*path_parts)
        self._update()

    def _update(self):
        for name in self.nl:
            name: str
            setattr(self, name, getattr(self.path, name))

    @observe(nl)
    def _change(self, e: ob_evt.TraitChangeEvent):
        setattr(self.path, e.name, e.new)
        self._update()
