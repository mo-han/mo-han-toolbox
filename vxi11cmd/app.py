#!/usr/bin/env python3
# encoding=utf8
import argparse

from core import win32_ctrl_c

try:
    from extra import VXI11CmdCustom as VXI11Cmd
except ImportError as e:
    from core import VXI11Cmd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--remote', metavar='<remote_addr>',
                        help='address of remote instrument')
    parser.add_argument('-c', '--command', nargs='+',
                        help='commands to be run once')
    parser.add_argument('-s', '--tcpserver', metavar='[listen_addr]:<port>',
                        help='start a tcp server listening on the given address')
    args = parser.parse_args()

    remote_addr = args.remote
    command_lines = args.command
    tcpserver_addr = args.tcpserver
    win32_ctrl_c()

    if remote_addr:
        cli = VXI11Cmd(remote_addr)
        if command_lines:
            cli.onecmd(' '.join(command_lines))
        elif tcpserver_addr:
            cli.do_tcpserver(tcpserver_addr)
        else:
            cli.cmdloop()
    elif tcpserver_addr:
        cli = VXI11Cmd()
        cli.do_tcpserver(tcpserver_addr)
    elif command_lines:
        cli = VXI11Cmd()
        cli.do_addr(None)
        cli.onecmd(' '.join(command_lines))
    else:
        cli = VXI11Cmd()
        cli.cmdloop()


main()
