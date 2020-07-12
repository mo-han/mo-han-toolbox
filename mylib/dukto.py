#!/usr/bin/env python3
# encoding=utf8

import ndrop.__main__
import ndrop.netdrop

from .tricks import modify_and_import
from .os_util import clipboard

_config = {'server_text_queue': None}


def config(new: dict = None, **kwargs):
    if new:
        _config.update(new)
    elif kwargs:
        _config.update(kwargs)
    else:
        for k in _config:
            print(repr(k), '=', repr(_config[k]))


def code_modify_ndrop_dukto_udp_pause(x: str):
    x = x.replace('''
class DuktoServer(Transport):
''', '''
class DuktoServer(Transport):
    udp_pause = 0.1
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


ndrop.netdrop.dukto\
    = ndrop_dukto_with_udp_pause\
    = modify_and_import('ndrop.dukto', code_modify_ndrop_dukto_udp_pause)


class NetDropServerX(ndrop.netdrop.NetDropServer):
    def recv_finish_text(self):
        logger = ndrop.netdrop.logger
        server_text_queue = _config['server_text_queue']
        data = self._file_io.getvalue()
        text = data.decode('utf-8')
        logger.info('TEXT: %s' % text)
        if server_text_queue:
            server_text_queue.put(text)
        self._file_io.close()
        self._file_io = None


ndrop.netdrop.NetDropServer \
    = ndrop.__main__.NetDropServer\
    = NetDropServerX


def run(**kwargs):
    if kwargs:
        config(**kwargs)
    ndrop.__main__.run()


def recv_text_into_clipboard():
    q = _config['server_text_queue']
    while 1:
        clipboard.set(q.get())
