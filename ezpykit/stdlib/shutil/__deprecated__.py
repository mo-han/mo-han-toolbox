#!/usr/bin/env python3
from shutil import rmtree

from ezpykit.stdlib import os


class FilesystemOperationError(Exception):
    pass


class FileToDirectoryError(FilesystemOperationError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class DirectoryToFileError(FilesystemOperationError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class NeitherFileNorDirectoryError(FilesystemOperationError):
    pass


def dir_is_empty(p):
    if not os.path.isdir(p):
        raise NotADirectoryError(p)
    return not bool(os.listdir(p))


def remove(p):
    try:
        os.remove(p)
    except PermissionError:
        try:
            rmtree(p)
        except NotADirectoryError:
            os.remove(p)
