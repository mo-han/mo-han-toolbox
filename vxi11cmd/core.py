# coding=utf8

import argparse
import cmd
import signal
import sys
from socketserver import TCPServer, BaseRequestHandler

import vxi11  # pip install -U python-vxi11

# PROMPT_LEFT_ARROW = '←'
PROMPT_LEFT_ARROW = '<-'

Vxi11Exception = vxi11.vxi11.Vxi11Exception


def win32_ctrl_c():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


class VXI11Cmd(cmd.Cmd):

    def __init__(self, address: str = None):
        super(VXI11Cmd, self).__init__()
        self.address = address
        if address:
            self.do_addr(address)
        self.lastcmd_return = None

    def postcmd(self, stop, line):
        self.lastcmd_return = stop
        return None

    def default(self, line):
        return self.do_cmd(line)

    def onecmd(self, line) -> str:
        try:
            r = super(VXI11Cmd, self).onecmd(line)
            ok = True
        except Vxi11Exception as e:
            r = 'VXI11 Error ' + e.msg
            ok = False
        except AttributeError as e:
            r = 'FAIL: ' + str(e)
            ok = False
        if not ok:
            print(r)
        return r

    def preloop(self):
        super(VXI11Cmd, self).preloop()
        self.do_help('')
        self.do_addr(self.address)
        self.prompt = 'VXI-11@{} {} '.format(self.address, PROMPT_LEFT_ARROW)
        for c in ['idn', 'remote']:
            self.onecmd(c)

    def do_cmd(self, line=None):
        """Send (SCPI) command."""
        command = line or input('Send command：')
        r = self.send_command(command)
        if r:
            print(r)
        return r

    def send_command(self, command):
        if command[-1] == '?':
            return self.inst.ask(command)
        else:
            return self.inst.write(command)

    # noinspection PyAttributeOutsideInit
    def do_addr(self, address):
        """Set remote address."""
        self.address = address or input('Remote address：')
        self.inst = vxi11.Instrument(self.address)
        return str((self.inst, self.inst.host, self.inst.client_id))

    def do_tcpserver(self, line: str):
        """
        Usage: tcpserver [ADDRESS]:PORT
        Start a TCP socket server as a command repeater, listing on [ADDRESS]:PORT.
        `ADDRESS`, if omitted, default to `localhost`.
        """
        try:
            host, port = line.split(':', maxsplit=1)
            host = host or 'localhost'
            port = int(port)
            self.tcpserver(host, port)
        except ValueError:
            print('Invalid server address: {}'.format(line))
            print('Usage: {}'.format(self.do_tcpserver.__doc__))

    def tcpserver(self, host: str, port: int):
        callback = self.onecmd
        welcome = f'vxi11cmd server, listen on {host}:{port}, connect to {self.address}.\n\n'.encode()

        class CmdServerHandler(BaseRequestHandler):
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
                        answer = callback(command)
                        if answer:
                            self.request.send(answer.encode() + b'\n')

        server = TCPServer((host, port), CmdServerHandler)
        server.serve_forever()

    @staticmethod
    def do_quit(*args):
        """Quit interactive CLI."""
        sys.exit(0)

    def do_local(self, *args):
        """Switch instrument into local mode."""
        try:
            self.inst.local()
        except Vxi11Exception:
            return self.do_cmd(':system:local')

    def do_remote(self, *args):
        """Switch instrument into remote mode."""
        try:
            return self.inst.remote()
        except Vxi11Exception:
            return self.do_cmd(':system:remote')

    def do_idn(self, *args):
        """Instrument identity."""
        return self.do_cmd('*idn?')
