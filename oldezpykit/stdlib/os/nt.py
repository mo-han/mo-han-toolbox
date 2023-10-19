#!/usr/bin/env python3
import time

from oldezpykit.stdlib.os.common import *
import subprocess


class EnVarKit(EnVarKit):
    path_sep = ';'
    reg_path = r'HKCU\Environment'
    use_reg_expand_sz = True

    @classmethod
    def save(cls, *args, **kwargs):
        for data in [*args, kwargs]:
            for k, v in data.items():
                cmd = ['reg', 'add', cls.reg_path, '/f', '/v', cls.valid_key(k), '/d', str(v)]
                if cls.use_reg_expand_sz:
                    cmd += ['/t', 'REG_EXPAND_SZ']
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL
                )
                # subprocess.run(['setx', str(k), str(v)])  # very slow
                # https://superuser.com/questions/565771/setting-user-environment-variables-is-very-slow
                # after setting user/machine scope environment variable
                # it calls native SendMessageTimeout function to notify any process about changes in environment
                # 1000 milliseconds (1 second) timeout is given to any recipient to process the message
        subprocess.run(['setx', 'LAST_SETX_TIMESTAMP', str(time.time())], stdout=subprocess.DEVNULL)

    @classmethod
    def get_saved_path_list(cls):
        r = subprocess.run(
            ['reg', 'query', cls.reg_path, '/v', 'PATH'],
            stdout=subprocess.PIPE, universal_newlines=True,
        )
        return r.stdout.strip().splitlines()[-1].strip().split(maxsplit=2)[-1].split(cls.path_sep)
