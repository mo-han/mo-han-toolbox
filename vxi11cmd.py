# coding=utf8

import cmd
import sys
import argparse

import vxi11
from lib_base import win32_ctrl_c


class VXI11Cmd(cmd.Cmd):
    doc_header = '命令列表'
    undoc_header = '命令列表（缺少说明）'

    def __init__(self, address: str = '', raw_print=False):
        super(VXI11Cmd, self).__init__()
        self.inst = None
        self.address = address
        self.print_method = print if raw_print else self.print_recv

    def preloop(self):
        super(VXI11Cmd, self).preloop()
        self.do_addr(self.address)
        self.do_help('')

    def default(self, line):
        self.do_msg(line)

    @staticmethod
    def print_recv(data):
        print('→ {}'.format(data))

    @staticmethod
    def do_quit(*args):
        """退出程序"""
        sys.exit(0)

    def do_addr(self, address, loud=True):
        """设置地址"""
        self.address = address or input('设备地址：')
        self.prompt = 'VXI-11@{} ← '.format(self.address)
        self.inst = vxi11.Instrument(self.address)
        self.inst.remote()
        if loud:
            self.do_idn()

    def do_msg(self, command):
        """发送消息"""
        command = command or input('消息：')
        if command[-1] == '?':
            try:
                self.print_method(self.inst.ask(command))
            except vxi11.vxi11.Vxi11Exception as e:
                self.print_method('!!! ERROR: {}'.format(e.args))
        else:
            self.inst.write(command)

    def do_idn(self, *args):
        """设备型号"""
        self.do_msg('*idn?')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--remote',
                        help='address of remote instrument')
    parser.add_argument('-c', '--command', nargs='+',
                        help='commands to be run once')
    return parser.parse_args()


def main(args: argparse.Namespace):
    if args.remote:
        if args.command:
            cli = VXI11Cmd(args.remote, raw_print=True)
            cmd = ' '.join(args.command)
            cli.do_addr(args.remote, loud=False)
            cli.onecmd(cmd)
        else:
            cli = VXI11Cmd(args.remote)
            cli.cmdloop()
    else:
        cli = VXI11Cmd()
        cli.cmdloop()


if __name__ == '__main__':
    win32_ctrl_c()
    main(parse_args())
