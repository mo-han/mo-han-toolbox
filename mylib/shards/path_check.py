#!/usr/bin/env python3
import errno
import os
import pathlib
import tempfile


# The code below is basically copied from an answer by Cecil Curry at:
# https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
# -*- CODE BLOCK BEGIN -*-

def is_path_valid(path: str) -> bool:
    """
    `True` if the passed path is a valid path for the current OS;
    `False` otherwise.
    """
    # if not isinstance(path, str):
    #     path = os.fsdecode(os.fspath(path))
    try:
        if not isinstance(path, str) or not path:
            return False
        if os.name == 'nt':
            drive, path = os.path.splitdrive(path)
            root = os.path.join(drive, os.path.sep)
            if not os.path.isdir(root):
                drive = os.environ.get('SystemDrive', 'C:')
                root = os.path.join(drive, os.path.sep)
            if not os.path.isdir(root):
                root = '.'
        else:
            root = os.path.sep
        for part in pathlib.PurePath(path).parts:
            try:
                os.lstat(os.path.join(root, part))
            except OSError as e:
                # If an OS-specific exception is raised, its error code
                # indicates whether this path is valid or not. Unless this
                # is the case, this exception implies an ignorable kernel or
                # filesystem complaint (e.g., path not found or inaccessible).
                #
                # Only the following exceptions indicate invalid paths:
                #
                # * Instances of the Windows-specific "WindowsError" class
                #   defining the "winerror" attribute whose value is
                #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
                #   fine-grained and hence useful than the generic "errno"
                #   attribute. When a too-long path is passed, for example,
                #   "errno" is "ENOENT" (i.e., no such file or directory) rather
                #   than "ENAMETOOLONG" (i.e., file name too long).
                # * Instances of the cross-platform "OSError" class defining the
                #   generic "errno" attribute whose value is either:
                #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
                #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
                if hasattr(e, 'winerror'):
                    if e.winerror == 123:
                        return False
                elif e.errno in (errno.ENAMETOOLONG, errno.ERANGE):
                    return False
    except TypeError as e:
        # if a "TypeError" exception was raised, it almost certainly has the
        # error message "embedded NUL character" indicating an invalid path.
        return False
    else:
        # If no exception was raised, all path components are valid,
        # and hence this path itself is valid.
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.


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
