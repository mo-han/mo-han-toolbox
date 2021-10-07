#!/usr/bin/env python3
from ._null import *


class EzEnVar(EzEnVar):
    @staticmethod
    def save(*args, **kwargs):
        envar_fp = f'~/.ezcolib_envar'
        profile_fp = f'~/.profile'
        the_line = f'test -f {envar_fp} && source {envar_fp}\n'
        with open(tilde_path(profile_fp), 'a+') as f:
            end = f.tell()
            f.seek(0)
            lines = f.readlines()
            if the_line not in lines:
                f.seek(end)
                f.write(the_line)
        with open(tilde_path(envar_fp), 'a+') as f:
            f.seek(0)
            envar = {}
            for line in f.readlines():
                if not line.startswith('export '):
                    continue
                line = line.split(' #', maxsplit=1)[0].strip()
                name, value = [s.strip(' "\'') for s in line.split('=', maxsplit=1)]
                envar[name] = value
            for data in [*args, kwargs]:
                envar.update(data)
            new_lines = [f'export "{name}={value}"\n' for name, value in data.items()]
            f.truncate()
            f.writelines(new_lines)
