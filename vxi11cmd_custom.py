#!/usr/bin/env python3
# encoding=utf8

import vxi11cmd


class VXI11CmdCustom(vxi11cmd.VXI11Cmd):
    DATA_ITEMS_TRIPLE = ['urms', 'umn', 'irms', 's', 'p', 'lamb', 'fu', ]
    DATA_ITEMS_SIGMA = ['urms', 'umn', 'irms', 's', 'p', 'lamb', ]
    DATA_ITEMS = [i + ',1' for i in DATA_ITEMS_TRIPLE] + \
                 [i + ',2' for i in DATA_ITEMS_TRIPLE] + \
                 [i + ',3' for i in DATA_ITEMS_TRIPLE] + \
                 [i + ',sigma' for i in DATA_ITEMS_SIGMA]
    DATA_ITEMS_NUM = len(DATA_ITEMS)
    DATA_ITEMS_CMD = ':num:num {}'.format(DATA_ITEMS_NUM)
    for i in range(DATA_ITEMS_NUM):
        DATA_ITEMS_CMD += ';:num:item{} {}'.format(i + 1, DATA_ITEMS[i])

    # def do_cmd(self, line=None):
    #     command = line or input('命令：')
    #     r = self.send_command(command)
    #     if r:
    #         if ';' in r:
    #             r = '\r\n'.join(r.split(';'))
    #         elif ',' in r:
    #             r = '\r\n'.join(r.split(','))
    #         print(r)
    #     return r

    def do_setdata(self, *args):
        self.do_remote()
        self.do_cmd(':wir v3a3')
        self.do_cmd(self.DATA_ITEMS_CMD)

    def do_getdata(self, *args):
        return self.do_cmd(':num:val?')

    def do_ct(self, line=None):
        msg = ':scal:ct'
        if line:
            msg = '{0} {1};{0}?'.format(msg, line)
        else:
            msg += '?'
        return self.do_cmd(msg)

    def do_vt(self, line=None):
        msg = ':scal:vt'
        if line:
            msg = '{0} {1};{0}?'.format(msg, line)
        else:
            msg += '?'
        return self.do_cmd(msg)
