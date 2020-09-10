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
    parser.add_argument('-c', '--command', nargs='+', metavar='arg',
                        help='commands to be run once')
    parser.add_argument('-l', '--tcp-relay', metavar='[listen_addr]:<port>',
                        help='start a tcp relay server listening on the given address')
    args = parser.parse_args()

    remote = args.remote
    conn_type = args.type
    timeout = args.timeout
    command_list = args.command
    relay_addr = args.tcp_relay
    win32_ctrl_c()

    if remote:
        shell = SCPIShell(address=remote, conn_type=conn_type, timeout=timeout)
        if command_list:
            shell.onecmd(' '.join(command_list))
        elif relay_addr:
            shell.do_tcprelay(relay_addr)
        else:
            shell.cmdloop()
    elif timeout or command_list:
        parser.error('--type, --timeout or --command has no effect when --remote is missing')
    elif relay_addr:
        shell = SCPIShell()
        shell.do_tcprelay(relay_addr)
    else:
        shell = SCPIShell()
        shell.cmdloop()


if __name__ == '__main__':
    run_cli_app()
