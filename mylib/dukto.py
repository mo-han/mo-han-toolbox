#!/usr/bin/env python3
# encoding=utf8
import ndrop.netdrop
import ndrop.__main__
from .tricks import modify_and_import


def code_modify_ndrop_dukto(x: str):
    x = x.replace('''
class DuktoServer(Transport):
''', '''
class DuktoServer(Transport):
    delay_after_udp_broadcast = 3
''')
    start = x.find('''
    def say_hello(self, dest):
''')
    x = x[:start] + x[start:].replace('''
            sock.close()
''','''
            logger.debug('Delay {}s after UDP unicast to {}:{}'.format(self.delay_after_udp_broadcast, *dest))
            time.sleep(self.delay_after_udp_broadcast)
            sock.close()
''')
    start = x.find('''
    def send_broadcast(self, data, port):
''')
    x = x[:start] + x[start:].replace('''

        sock.close()
''', '''
        logger.debug('Delay {}s after UDP broadcast'.format(self.delay_after_udp_broadcast))
        time.sleep(self.delay_after_udp_broadcast)
        sock.close()
''')
    return x


ndrop.netdrop.dukto = modified_ndrop_dukto = modify_and_import('ndrop.dukto', code_modify_ndrop_dukto)
ndrop_run = ndrop.__main__.run
