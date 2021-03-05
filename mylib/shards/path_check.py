#!/usr/bin/env python3
import errno
import os
import pathlib
import tempfile


# -*- CODE BLOCK BEGIN -*-
# The code below is copied and modified from an answer by Cecil Curry at:
# https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855

def is_path_valid(path: str) -> bool:
    try:
        if not isinstance(path, str) or not path:
            return False
        if os.name == 'nt':
            drive, path = os.path.splitdrive(path)
            if not os.path.isdir(drive):
                drive = os.environ.get('SystemDrive', 'C:')
            if not os.path.isdir(drive):
                drive = ''
        else:
            drive = ''
        parts = pathlib.Path(path).parts
        check_list = [os.path.join(*parts), *parts]
        for x in check_list:
            try:
                os.lstat(drive + x)
            except OSError as e:
                if hasattr(e, 'winerror') and e.winerror == 123:
                    return False
                elif e.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError:
        return False
    else:
        return True


def is_path_creatable(path: str) -> bool:
    """
    `True` if the current user has sufficient permissions to create the passed
    path; `False` otherwise.
    """
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dirname = os.path.dirname(path) or os.getcwd()
    return os.access(dirname, os.W_OK)


def is_path_existent_or_creatable(path: str) -> bool:
    """
    `True` if the passed path is a valid path for the current OS _and_
    either currently exists or is hypothetically creatable; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    """
    try:
        # To prevent "os" module calls from raising undesirable exceptions on
        # invalid path, is_path_valid() is explicitly called first.
        return is_path_valid(path) and (
                os.path.exists(path) or is_path_creatable(path))
    # Report failure on non-fatal filesystem complaints (e.g., connection
    # timeouts, permissions issues) implying this path to be inaccessible. All
    # other exceptions are unrelated fatal issues and should not be caught here.
    except OSError:
        return False


def is_path_probably_creatable(path: str) -> bool:
    """
    `True` if the current user has sufficient permissions to create **siblings**
    (i.e., arbitrary files in the parent directory) of the passed path;
    `False` otherwise.
    """
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dirname = os.path.dirname(path) or os.getcwd()

    try:
        # For safety, explicitly close and hence delete this temporary file
        # immediately after creating it in the passed path's parent directory.
        with tempfile.TemporaryFile(dir=dirname):
            pass
        return True
    # While the exact type of exception raised by the above function depends on
    # the current version of the Python interpreter, all such types subclass the
    # following exception superclass.
    except EnvironmentError:
        return False


def is_path_existent_or_probably_creatable(path: str) -> bool:
    """
    `True` if the passed path is a valid path on the current OS _and_
    either currently exists or is hypothetically creatable in a cross-platform
    manner optimized for POSIX-unfriendly filesystems; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    """
    try:
        # To prevent "os" module calls from raising undesirable exceptions on
        # invalid path, is_path_valid() is explicitly called first.
        return is_path_valid(path) and (
                os.path.exists(path) or is_path_probably_creatable(path))
    # Report failure on non-fatal filesystem complaints (e.g., connection
    # timeouts, permissions issues) implying this path to be inaccessible. All
    # other exceptions are unrelated fatal issues and should not be caught here.
    except OSError:
        return False

# -*- CODE BLOCK END -*-
