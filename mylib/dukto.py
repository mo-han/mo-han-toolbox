#!/usr/bin/env python3
# encoding=utf8

import ndrop.__main__
import ndrop.netdrop
import ndrop.shell

from .os_util import clipboard, ensure_open_file
from .tricks import modify_and_import, Attreebute

config_at = Attreebute()
config_at.server.text.queue = None
config_at.server.echo = False


def echo_after_recv(client_address):
    if config_at.server.echo:
        client = ndrop.netdrop.NetDropClient(client_address[0], mode='dukto')
        client.send_text('# DUKTO.ECHO.RECV')


def code_modify_ndrop_dukto(x: str):
    x = x.replace('''
class DuktoServer(Transport):
''', '''
class DuktoServer(Transport):
    udp_pause = 0.01
''')
    start = x.find('''def send_broadcast(self, data, port):''')
    x = x[:start] + x[start:].replace(
        '''.sendto(data, (broadcast, port))''',
        '''.sendto(data, (broadcast, port));'''
        '''logger.debug('Pause {}s after UDP to {}:{}'.format(self.udp_pause, broadcast, port));'''
        '''time.sleep(self.udp_pause)'''
    )
    start = x.find('''def say_hello(self, dest):''')
    x = x[:start] + x[start:].replace(
        '''.sendto(data, dest)''',
        '''.sendto(data, dest);'''
        '''logger.debug('Pause {}s after UDP to {}:{}'.format(self.udp_pause, *dest));'''
        '''time.sleep(self.udp_pause)'''
    )
    start = x.find('class TCPHandler(socketserver.BaseRequestHandler):')
    x = x[:start] + x[start:].replace(
        'self._packet.unpack_tcp(self.server.agent, self._recv_buff)',
        'self._packet.client_address = self.client_address;'
        'self._packet.unpack_tcp(self.server.agent, self._recv_buff)'
    )
    start = x.find('def unpack_tcp(self, agent, data):')
    x = x[:start] + x[start:].replace(
        'agent.recv_finish_file(self._filename)',
        'agent.recv_finish_file(self._filename);'
        'echo_after_recv(self.client_address)'
    )
    return x


class NetDropServerX(ndrop.netdrop.NetDropServer):
    def recv_finish_text(self):
        logger = ndrop.netdrop.logger
        data = self._file_io.getvalue()
        text = data.decode('utf-8')
        logger.info('TEXT: %s' % text)
        self._file_io.close()
        self._file_io = None
        queue = config_at.server.text.queue
        if queue:
            queue.put(text)

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


ndrop.netdrop.dukto = modify_and_import('ndrop.dukto', code_modify_ndrop_dukto)
ndrop.netdrop.dukto.echo_after_recv = echo_after_recv
ndrop.netdrop.dukto.get_system_symbol = ndrop.netdrop.nitroshare.get_system_symbol = get_system_symbol
ndrop.__main__.NetDropServer = NetDropServerX
ndrop.__main__.NetDropShell = NetDropShellX


def run(**kwargs):
    for k, v in kwargs.items():
        config_at[k.replace('_', '.')] = v
    ndrop.__main__.run()


def copy_recv_text(file: str = None, use_clipboard: bool = False):
    queue = config_at.server.text.queue
    if file:
        def handle(t):
            with ensure_open_file(file, 'a') as f:
                f.write(t + '\n')
                ndrop.netdrop.logger.info("Copy TEXT to file '{}'".format(file))
    elif use_clipboard:
        def handle(t):
            clipboard.set(t)
            ndrop.netdrop.logger.info('Copy TEXT to clipboard')
    else:
        def handle(t):
            pass

    while 1:
        text = queue.get()
        handle(text)
