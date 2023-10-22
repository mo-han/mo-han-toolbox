# coding=utf8
import cmd
import logging
import signal
import sys
from socket import timeout as SocketTimeout
from socketserver import ThreadingTCPServer, StreamRequestHandler
from urllib.parse import urlparse

import vxi11  # pip install -U python-vxi11
from serial import Serial, SerialException

from oldezpykit.metautil import Stopwatch

S_VXI11 = 'vxi11'
S_SERIAL = 'serial'
S_YOKOGAWA_ETHERNET_LEGACY = 'yokogawa-ethernet-legacy'
# PROMPT_LEFT_ARROW = '←'
PROMPT_LEFT_ARROW = '<-'

Vxi11Exception = vxi11.vxi11.Vxi11Exception

__logger__ = logging.getLogger(__name__)


class EmptyTimeout(Exception):
    pass


def win32_ctrl_c():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


def tolerant_urlparse(url: str, default_prefix='scheme://'):
    if '://' not in url:
        url = default_prefix + url
    r = urlparse(url)
    return r


def str2eval(x: str):
    from ast import literal_eval
    try:
        return literal_eval(x)
    except (ValueError, SyntaxError):
        return x


def str2float2str(s: str):
    try:
        return str(float(s))
    except ValueError:
        return s


def p_return(x):
    if x is not None:
        print(x)
    return x


def pp_return(x):
    if x is not None:
        pp_return(x)
    return x


class LinkWrapper:
    def __init__(self, link):
        # self.__dict__['_link'] = self._link = link
        self._link = link

    # @property
    # def members(self):
    #     return {k: v.__doc__ if isinstance(v, Callable) else v for k, v in inspect.getmembers(self._link) if
    #             k[:2] + k[-2:] != '____' and not isinstance(v, Callable) or k in ('__class__',)}
    #
    # def __setattr__(self, key, value):
    #     setattr(self._link, key, value)
    #
    # def __getattr__(self, key):
    #     return getattr(self._link, key)


class YokogawaEthernetLegacyWrapper(LinkWrapper):
    HEAD_MAX_SIZE = b'\x00\x04\x00\x00'
    MAX_SIZE = int.from_bytes(HEAD_MAX_SIZE, 'big')

    def __init__(self, address):
        from socket import socket, AF_INET, SOCK_STREAM
        s = socket(AF_INET, SOCK_STREAM)
        super().__init__(s)
        u = tolerant_urlparse(address, 'tcp://')
        self.hostname = u.hostname
        self.port = u.port or 10001
        self.username = u.username or 'anonymous'
        self.password = u.password or ''
        s.connect((self.hostname, self.port))
        self.wait('username:')
        self.write(self.username)
        self.wait('')
        self.wait('password:')
        self.write(self.password)
        self.wait('')
        msg = self.read()
        if not msg.endswith('is ready.'):
            raise ConnectionRefusedError(msg)

    def wait(self, s: str):
        while True:
            if self.read() == s:
                break

    def _read_exact_size(self, size: int):
        recv_into = self._link.recv_into
        buffer = memoryview(bytearray(size))
        t = Stopwatch().start()
        while size:
            n = recv_into(buffer[-size:])
            if not n:
                raise ConnectionError('tcp socket remote peer disconnect')
            size -= n
        __logger__.debug(('exact size', len(buffer), f'{t.stop():.6f}s'))
        return buffer

    def _read_0x80(self, head):
        n = int.from_bytes(head[1:], 'big')
        body = self._read_exact_size(n)
        return body

    def read_binary(self):
        head = self._read_exact_size(4)
        if head[:1] == b'\x80':
            return self._read_0x80(head)
        body = bytearray()
        while head == self.HEAD_MAX_SIZE:
            body.extend(self._read_exact_size(self.MAX_SIZE))
            head = self._read_exact_size(4)
        if head[:1] == b'\x80':
            body.extend(self._read_0x80(head))
            return memoryview(body)
        else:
            raise ValueError('unknown head', bytes(head))

    def read_block_data(self):
        bv = self.read_binary()
        if bv[-1:] != b'\n':
            raise ValueError('no <RMT> at end', bytes(bv[-16:]))
        bv = bv[:-1]
        if bv[:1] == b'#':
            digits_n = int(bv[1:2])
            digits_stop_i = 2 + digits_n
            n = int(bv[2:digits_stop_i])
            r = bv[digits_stop_i:]
            if len(r) != n:
                raise ValueError('data length not match', str(bv[:digits_stop_i], 'ascii'), len(r))
        elif bv[:2] == b'"#':  # left quote
            digits_n = int(bv[2:3])
            digits_stop_i = 3 + digits_n
            n = int(bv[3:digits_stop_i])
            r = bv[digits_stop_i + 1:]  # skip right quote
            if len(r) != n:
                raise ValueError('data length not match', str(bv[:digits_stop_i], 'ascii'), len(r))
        else:
            raise ValueError('invalid format for block data, missing #N head')
        return r

    def read(self):
        b = self.read_binary()
        try:
            s = str(b, 'ascii').strip()
        except UnicodeDecodeError as e:
            i = e.start
            s = f'UnicodeDecodeError at {i}: {bytes(b[i - 16:i])} | {bytes(b[i:i + 1])} | {bytes(b[i + 1:i + 17])}'
        return s

    def write(self, s: str):
        b = s.encode()
        head = b'\x80\x00' + len(b).to_bytes(2, 'big')
        self._link.send(head + b)

    def ask(self, s: str):
        self.write(s)
        return self.read()

    def timeout(self, timeout=None):
        if timeout is not None:
            self._link.settimeout(timeout)
        return self._link.gettimeout()

    def __str__(self):
        return f'YOKOGAWA Ethernet (Legacy): ' \
               f'URL=tcp://{self.hostname}:{self.port}, ' \
               f'username={self.username}, ' \
               f'password={self.password}, ' \
               f'socket={self._link}'


class SerialLinkWrapper(LinkWrapper):
    def __init__(self, serial: Serial):
        super(SerialLinkWrapper, self).__init__(serial)

    def read(self):
        d = self._link.read_until().decode()
        if d:
            return d
        else:
            raise EmptyTimeout

    def write(self, s: str):
        self._link.read_all()
        self._link.write(f'{s}\n'.encode())

    def ask(self, s: str):
        self.write(s)
        return self.read()

    def timeout(self, timeout=None):
        if timeout is not None:
            self._link.timeout = timeout
        return self._link.timeout

    def __str__(self):
        return f'{self._link.port}: {self._link}'


class VXI11LinkWrapper(LinkWrapper):
    def __init__(self, inst: vxi11.Instrument):
        super(VXI11LinkWrapper, self).__init__(inst)
        self.ask = inst.ask
        self.read = inst.read
        self.write = inst.write

    def timeout(self, timeout=None):
        if timeout is not None:
            self._link.timeout = timeout
        return self._link.timeout

    def __str__(self):
        return f'{self._link.host}: {self._link}'


class SCPIShell(cmd.Cmd):
    # intro = f'communicate with a remote instrument via SCPI commands\n'
    default_conn_type = 'VXI-11'
    default_timeout = None

    def __init__(self, address: str = None, conn_type: str = None, timeout: float = None):
        self.address = address
        self.conn_type = conn_type or self.default_conn_type
        self.link = None
        self.ask = None
        self.read = None
        self.write = None
        self.lastcmd_return = None
        self.connected = False
        self.verbose = 0
        super(SCPIShell, self).__init__()
        if self.address:
            self.connect(address, conn_type, timeout)

    def do_verbose(self, line):
        self.verbose = int(line)

    def postcmd(self, stop, line):
        self.lastcmd_return = stop
        return None

    def default(self, line):
        return self.do_scpi(line)

    def onecmd(self, line) -> str:
        ok = False
        try:
            r = super(SCPIShell, self).onecmd(line)
            ok = True
        except Vxi11Exception as e:
            r = f'! error (vxi11): {e.msg}'
        except SerialException as e:
            r = f'! error (serial): {e}'
        except AttributeError as e:
            r = f'! error (attribute): {str(e)}'
        except EmptyTimeout:
            r = f"! error (timeout): '{line}'"
        except SocketTimeout:
            r = '! error (socket): timeout'
        if ok:
            return r
        else:
            print(r)

    def preloop(self):
        super(SCPIShell, self).preloop()
        self.do_help('')
        if not self.connected:
            address = input('Connect to: ')
            conn_type_list = ('VXI-11', 'Serial', S_YOKOGAWA_ETHERNET_LEGACY)
            conn_type_default = conn_type_list[0]
            conn_type_choose_str_list = []
            for i in range(len(conn_type_list)):
                conn_type_choose_str_list.append(f'{i + 1}={conn_type_list[i]}')
            conn_type_choose_str_list.append(f'default={conn_type_default}')
            choose = input(
                f'Connection Type ({", ".join(conn_type_choose_str_list)}): '
            ).strip()
            if choose == '':
                conn_type = conn_type_default
            else:
                conn_type = conn_type_list[int(choose) - 1]
            timeout = input('Connection timeout in seconds (default=None): ').strip()
            if timeout == '':
                timeout = None
            else:
                timeout = float(timeout)
            print(self.connect(address, conn_type, timeout))
        self.prompt = f'{self.conn_type}@{self.address} {PROMPT_LEFT_ARROW} '
        for c in ['idn', 'remote']:
            self.onecmd(c)

    def do_scpi(self, line=None):
        """Send (SCPI) command."""
        command = line or input('Send command：')
        if self.verbose:
            print(f'{self.prompt}`{command}`')
        return p_return(self.send_scpi(command))

    def send_scpi(self, command):
        if command.endswith('?'):
            return self.ask(command)
        else:
            self.write(command)

    # def link_config(self, key=None, value=None):
    #     if key is None:
    #         return self.link
    #     if value is None:
    #         return getattr(self.link, key)
    #     else:
    #         setattr(self.link, key, value)
    #
    # def do_link_config(self, line):
    #     """get or set attribution of underlying link:
    #     attr <key_name>
    #     attr <key_name> <new_value>
    #     """
    #     args = line.split(maxsplit=1)
    #     if not args:
    #         return f"{self.link_config()}\n{self.link_config('members')}"
    #     elif len(args) == 1:
    #         key = args[0]
    #         value = self.link_config(key)
    #         if key == 'members':
    #             return pformat(value)
    #         else:
    #             return value
    #     else:
    #         self.link_config(args[0], literal_eval(args[-1]))

    def do_timeout(self, line):
        from ast import literal_eval
        try:
            timeout = literal_eval(line)
        except (SyntaxError, ValueError):
            timeout = None
        try:
            return p_return(self.link.timeout(timeout))
        except Exception as e:
            print(f'! {e} <{e!r}>')

    def connect(self, address=None, conn_type=None, timeout=None):
        self.address = address = address or self.address
        self.conn_type = conn_type = conn_type or self.conn_type
        timeout = timeout or self.default_timeout
        conn_type_lower = conn_type.lower()
        if conn_type_lower.startswith('vxi'):
            inst = vxi11.Instrument(address)
            if timeout is not None:
                inst.timeout = timeout
            self.link = VXI11LinkWrapper(inst)
            self.ask = self.link.ask
            self.write = self.link.write
            self.read = self.link.read
        elif conn_type_lower.startswith(S_SERIAL):
            if address.total(':'):
                port, setting = address.split(':', maxsplit=1)
                if setting.total(','):
                    baud, bits = setting.split(',', maxsplit=1)
                    data_bits, parity_bit, stop_bits = bits
                    com = Serial(port=port, baudrate=int(baud), bytesize=int(data_bits), parity=parity_bit.upper(),
                                 stopbits=int(stop_bits))
                else:
                    com = Serial(port=port, baudrate=int(setting))
            else:
                com = Serial(address)
            com.timeout = timeout
            self.link = SerialLinkWrapper(com)
            self.ask = self.link.ask
            self.write = self.link.write
            self.read = self.link.read
        elif conn_type_lower.startswith(S_YOKOGAWA_ETHERNET_LEGACY):
            self.link = YokogawaEthernetLegacyWrapper(address)
            self.ask = self.link.ask
            self.write = self.link.ask
            self.read = self.link.read
            if timeout:
                self.link._link.settimeout(timeout)
        else:
            raise NotImplementedError(conn_type)
        self.connected = True
        return str(self.link)

    def do_connect(self, line=None):
        """Set link to remote:
        connect <address>
        connect <address> <connection_type>
        connect <address> <connection_type> <timeout>
        """
        if not line:
            address, conn_type, timeout = None, None, None
        else:
            args = line.split()
            while len(args) < 3:
                args.append(None)
            address, conn_type, timeout = args
        print(self.connect(address, conn_type, timeout))

    def do_disconnect(self, *noargs):
        """close current underlying link"""
        self.link.close()

    def do_tcprelay(self, line: str):
        """Usage: tcpserver [ADDRESS]:PORT
        Start a TCP socket server as a command repeater, listing on [ADDRESS]:PORT.
        `ADDRESS`, if omitted, default to `localhost`.
        """
        try:
            host, port = line.split(':', maxsplit=1)
            host = host or 'localhost'
            port = int(port)
            self.tcprelay(host, port)
        except ValueError:
            print('Invalid server address: {}'.format(line))
            print('Usage: {}'.format(self.do_tcprelay.__doc__))

    def tcprelay(self, host: str, port: int):
        callback = self.onecmd
        welcome = f'scpi relay server {host}:{port}, remote {self.address}.\r\n\r\n'.encode()

        class CmdServerHandler(StreamRequestHandler):
            def handle(self):
                self.request.send(welcome)
                buffer = bytearray()
                while True:
                    buffer.extend(self.request.recv(64))
                    while True:
                        i = buffer.find(b'\n')
                        if i == -1:
                            break
                        line = bytes(buffer[:i + 1])
                        buffer[:] = buffer[i + 1:]
                        command = line.decode().strip()
                        print(command)
                        try:
                            answer = callback(command)
                            if answer:
                                self.request.send(answer.encode() + b'\r\n')
                        except KeyboardInterrupt:
                            sys.exit(2)
                        except Exception as e:
                            self.request.send(str(e).encode() + b'\r\n')

        server = ThreadingTCPServer((host, port), CmdServerHandler)
        server.serve_forever()

    @staticmethod
    def do_quit(*args):
        """Quit interactive CLI."""
        sys.exit(0)

    def do_local(self, *args):
        """Switch instrument into local mode."""
        return self.do_scpi(':communicate:remote 0')

    def do_remote(self, *args):
        """Switch instrument into remote mode."""
        return self.do_scpi(':communicate:remote 1')

    def do_idn(self, *args):
        """Instrument identity."""
        return self.do_scpi('*idn?')
