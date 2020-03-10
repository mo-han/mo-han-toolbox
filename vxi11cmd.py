# coding=utf8

import cmd
import sys

import vxi11


class VXI11Cmd(cmd.Cmd):
    doc_header = '命令列表'
    doc_header += ' ' * len(doc_header)
    undoc_header = '命令列表（无说明）'
    undoc_header += ' ' * len(undoc_header)

    def __init__(self, address: str = ''):
        super(VXI11Cmd, self).__init__()
        self.inst = None
        self.address = address

    def preloop(self):
        super(VXI11Cmd, self).preloop()
        self.do_addr(self.address)
        self.do_help('')

    @staticmethod
    def print_recv(data):
        print('→ {}'.format(data))

    @staticmethod
    def do_quit(*args):
        """退出程序"""
        exit(0)

    def do_addr(self, address):
        """设置地址"""
        self.address = address or input('设备地址：')
        self.prompt = 'VXI-11@{} ← '.format(self.address)
        self.inst = vxi11.Instrument(self.address)
        self.inst.remote()
        self.do_idn()

    def do_msg(self, command):
        """发送消息"""
        command = command or input('消息：')
        if command[-1] == '?':
            self.print_recv(self.inst.ask(command))
        else:
            self.inst.write(command)

    def do_idn(self, *args):
        """设备型号"""
        self.do_msg('*idn?')


if __name__ == '__main__':
    try:
        cli = VXI11Cmd(sys.argv[1])
    except IndexError:
        cli = VXI11Cmd()
    cli.cmdloop()
