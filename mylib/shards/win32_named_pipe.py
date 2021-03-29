#!/usr/bin/env python3
# https://codereview.stackexchange.com/questions/88672/python-wrapper-for-windows-pipes

import io
import msvcrt

import win32api
import win32file
import win32pipe

PIPE_ROOT = r'\\.\pipe' '\\'


class Win32NamedPipe(io.IOBase):
    def __init__(self, name, pipe_type='server' or 'client', *,
                 open_mode=win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                 pipe_mode=win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_NOWAIT,
                 maxinstances=255,
                 out_buffer_size=1000000,
                 in_buffer_size=1000000,
                 default_timeout=50,
                 security_attrib=None):
        """An implementation of a file-like python object pipe
        https://msdn.microsoft.com/en-us/library/windows/desktop/aa365150(v=vs.85).aspx"""
        self.pipe_type = pipe_type
        self.name = name
        self.open_mode = open_mode
        self.pipe_mode = pipe_mode
        if pipe_type == 'server':
            self.handle = win32pipe.CreateNamedPipe(
                PIPE_ROOT + name,
                open_mode,  # default PIPE_ACCESS_DUPLEX|FILE_FLAG_OVERLAPPED
                pipe_mode,  # default PIPE_TYPE_BYTE|PIPE_NOWAIT
                maxinstances,  # default 255
                out_buffer_size,  # default 1000000
                in_buffer_size,  # default 1000000
                default_timeout,  # default 50
                security_attrib  # default None
            )
        elif pipe_type == 'client':
            # it doesn't matter what type of pipe the server is so long as we know the name
            self.handle = win32file.CreateFile(
                PIPE_ROOT + name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
        else:
            raise ValueError('pipe_type', ('server', 'client'))
        self.fd = msvcrt.open_osfhandle(self.handle, 0)
        self.is_connected = False
        self.flags, self.out_buffer_size, self.in_buffer_size, self.maxinstances = win32pipe.GetNamedPipeInfo(
            self.handle)

    def connect(self):  # TODO: WaitNamedPipe ?
        win32pipe.ConnectNamedPipe(self.handle, None)
        self.is_connected = True

    def __del__(self):
        try:
            self.write(b'')  # try to clear up anyone waiting
        except win32pipe.error:  # no one's listening
            pass
        self.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def isatty(self):  # Return True if the stream is interactive (i.e., connected to a terminal/tty device).
        return False

    def seekable(self):
        return False

    def fileno(self):
        return self.fd

    def seek(self, *args):  # seek family
        raise NotImplementedError('seek not implemented for win32 named pipe')

    def tell(self):  # Part of the seek family. Not supported
        raise NotImplementedError('tell not implemented for win32 named pipe')

    def write(self, data):  # WriteFileEx impossible due to callback issues.
        if not self.is_connected and self.pipe_type == 'server':
            self.connect()
        win32file.WriteFile(self.handle, data)
        return len(data)

    def close(self):
        win32pipe.DisconnectNamedPipe(self.handle)

    def read(self, n=None):
        if n is None:
            n = self.in_buffer_size
        ret_int, data = win32file.ReadFile(self.handle, n)
        if ret_int != 0:
            raise BrokenPipeError(win32api.FormatMessage(ret_int))
        else:
            return data
