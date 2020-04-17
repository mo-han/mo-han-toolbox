# coding=utf8

import argparse
import cmd
import signal
import sys
from socketserver import TCPServer, BaseRequestHandler

import vxi11

PROMPT_LEFT_ARROW = '←'


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

    def preloop(self):
        super(VXI11Cmd, self).preloop()
        self.do_help('')
        self.do_addr(self.address)
        self.do_idn()
        self.do_remote()
        self.prompt = 'VXI-11@{} {} '.format(self.address, PROMPT_LEFT_ARROW)

    def do_cmd(self, line=None):
        command = line or input('命令：')
        r = self.send_command(command)
        if r:
            print(r)
        return r

    def send_command(self, command):
        if command[-1] == '?':
            try:
                return self.inst.ask(command)
            except vxi11.vxi11.Vxi11Exception as e:
                return 'FAIL: {}'.format(str(e))
        else:
            return self.inst.write(command)

    # noinspection PyAttributeOutsideInit
    def do_addr(self, address):
        self.address = address or input('设备地址：')
        self.inst = vxi11.Instrument(self.address)
        return str((self.inst, self.inst.host, self.inst.client_id))

    def do_tcpserver(self, line: str):
        """tcpserver [host]:port"""
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
        welcome = 'vxi11cmd server, listening on port {}:{}, connected to remote {}.\r\n\r\n'
        welcome = welcome.format(host, port, self.address).encode()

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
                        else:
                            line = bytes(buffer[:i + 1])
                            buffer[:] = buffer[i + 1:]
                            command = line.decode().strip()
                            print(command)
                            try:
                                answer = callback(command)
                            except AttributeError as e:
                                answer = 'FAIL: {}'.format(str(e))
                            if answer:
                                self.request.send(answer.encode() + b'\r\n')

        server = TCPServer((host, port), CmdServerHandler)
        server.serve_forever()

    @staticmethod
    def do_quit(*args):
        sys.exit(0)

    def do_local(self, args):
        self.inst.local()

    def do_remote(self, *args):
        return self.inst.remote()

    def do_idn(self, *args):
        return self.do_cmd('*idn?')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--remote',
                        help='address of remote instrument')
    parser.add_argument('-c', '--command', nargs='+',
                        help='commands to be run once')
    parser.add_argument('-s', '--tcpserver',
                        help='start a tcp server listening on the given address')
    return parser.parse_args()


def main(args: argparse.Namespace):
    try:
        # noinspection PyUnresolvedReferences
        import vxi11cmd_custom
        _vxi11cmd = vxi11cmd_custom.VXI11CmdCustom
    except ImportError:
        _vxi11cmd = VXI11Cmd

    remote_addr = args.remote
    command_lines = args.command
    tcpserver_addr = args.tcpserver

    if remote_addr:
        cli = _vxi11cmd(remote_addr)
        if command_lines:
            cli.onecmd(' '.join(command_lines))
        elif tcpserver_addr:
            cli.do_tcpserver(tcpserver_addr)
        else:
            cli.cmdloop()
    elif tcpserver_addr:
        cli = _vxi11cmd()
        cli.do_tcpserver(tcpserver_addr)
    elif command_lines:
        cli = _vxi11cmd()
        cli.do_addr(None)
        cli.onecmd(' '.join(command_lines))
    else:
        cli = _vxi11cmd()
        cli.cmdloop()


if __name__ == '__main__':
    win32_ctrl_c()
    main(parse_args())
