#!/usr/bin/env python3
# encoding=utf8
import argparse

from core import win32_ctrl_c

try:
    from extra import SCPIShellCustom as SCPIShell
except ImportError as e:
    from core import SCPIShell


def run_cli_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--remote',
                        help='address or port or link of remote instrument')
    parser.add_argument('-t', '--type', default='VXI-11',
                        help='connection type: vxi11, serial')
    parser.add_argument('-o', '--timeout', type=float,
                        help='connection timeout')
    parser.add_argument('-c', '--command', nargs='+', metavar='args',
                        help='commands to be run once')
    parser.add_argument('-s', '--tcpserver', metavar='[listen_addr]:<port>',
                        help='start a tcp server listening on the given address')
    args = parser.parse_args()

    remote = args.remote
    conn_type = args.type
    timeout = args.timeout
    command_list = args.command
    tcpserver_addr = args.tcpserver
    win32_ctrl_c()

    if remote:
        cli = SCPIShell(address=remote, conn_type=conn_type, timeout=timeout)
        if command_list:
            cli.onecmd(' '.join(command_list))
        elif tcpserver_addr:
            cli.do_tcpserver(tcpserver_addr)
        else:
            cli.cmdloop()
    else:
        cli = SCPIShell()
        cli.cmdloop()


if __name__ == '__main__':
    run_cli_app()
