#!/usr/bin/env python3
# encoding=utf8

import ndrop.__main__
import ndrop.netdrop
import ndrop.shell

from .os_util import clipboard, ensure_open_file
from .tricks import modify_and_import, Attree

config_at = Attree()
config_at.server.text.queue = None


def code_modify_ndrop_dukto_udp_pause(x: str):
    x = x.replace('''
class DuktoServer(Transport):
''', '''
class DuktoServer(Transport):
    udp_pause = 0.01
''')
    start = x.find('''def send_broadcast(self, data, port):''')
    x = x[:start] + x[start:].replace(
        '''.sendto(data, (broadcast, port))''',
        '''.sendto(data, (broadcast, port));''' +
        '''logger.debug('Pause {}s after UDP to {}:{}'.format(self.udp_pause, broadcast, port));''' +
        '''time.sleep(self.udp_pause)'''
    )
    start = x.find('''def say_hello(self, dest):''')
    x = x[:start] + x[start:].replace(
        '''.sendto(data, dest)''',
        '''.sendto(data, dest);''' +
        '''logger.debug('Pause {}s after UDP to {}:{}'.format(self.udp_pause, *dest));''' +
        '''time.sleep(self.udp_pause)'''
    )
    return x


class NetDropServerX(ndrop.netdrop.NetDropServer):
    def recv_finish_text(self):
        logger = ndrop.netdrop.logger
        data = self._file_io.getvalue()
        text = data.decode('utf-8')
        logger.info('TEXT: %s' % text)
        queue = config_at.server.text.queue
        if queue:
            queue.put(text)
        self._file_io.close()
        self._file_io = None

    def get_nodes(self):
        nodes = []
        for transport in self._transport:
            for k, n in transport._nodes.items():
                nodes.append({
                    'mode': transport._name,
                    'ip': k,
                    'port': n['port'],
                    'user': n.get('user', 'n/a'),
                    'name': n['name'],
                    'os': n['operating_system'],
                    'format': transport.format_node()
                })
        return nodes


class NetDropShellX(ndrop.shell.NetDropShell):
    def do_node(self, arg):
        """List online nodes."""
        nodes = self._server.get_nodes()
        if not nodes:
            print('[]')
            return
        i = 0
        for node in nodes:
            i += 1
            print('[{}] {ip}:{port} -- {user} at {name} ({os}) -- {mode} server on {format}'.format(i, **node))


def get_system_symbol(system):
    symbols = {
        'darwin': 'Mac',
        'windows': 'Win',
    }
    return symbols.get(system.lower(), system)


ndrop.netdrop.dukto = modify_and_import('ndrop.dukto', code_modify_ndrop_dukto_udp_pause)
ndrop.netdrop.dukto.get_system_symbol = ndrop.netdrop.nitroshare.get_system_symbol = get_system_symbol
ndrop.__main__.NetDropServer = NetDropServerX
ndrop.__main__.NetDropShell = NetDropShellX


def run(**kwargs):
    if kwargs:
        config_at(**kwargs)
    ndrop.__main__.run()


def copy_recv_text(file: str = None, use_clipboard: bool = False):
    queue = config_at.server.text.queue
    while 1:
        text = queue.get()
        if file:
            with ensure_open_file(file, 'a') as f:
                f.write(text + '\n')
                ndrop.netdrop.logger.info("Copy TEXT to file '{}'".format(file))
        if use_clipboard:
            clipboard.set(text)
            ndrop.netdrop.logger.info('Copy TEXT to clipboard')
