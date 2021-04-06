#!/usr/bin/env python3

import tabulate

from mylib import fstk_lite
from mylib.ez import *
from mylib.ez import argparse

__dirname__, __stem__, _ = fstk_lite.split_dirname_basename_ext(__file__)
apr = argparse.ArgumentParserRigger()
an = apr.an
meta_apr = argparse.ArgumentParserRigger()


@functools.lru_cache()
def find_module_path():
    r = {}
    with fstk_lite.ctx_pushd(__dirname__):
        for f in next(os.walk('.'))[-1]:
            match = re.match(rf'({__stem__})_(.+)\.py', f)
            if not match:
                continue
            name = match.group(2)
            r[name] = fstk_lite.make_path(__dirname__, f)
    return r


an.l = an.list = None


@meta_apr.root()
@meta_apr.true(an.l, an.list)
@meta_apr.map(list_cmd=an.list)
def meta_cmd(list_cmd):
    if list_cmd:
        root_dir = os.path.commonpath(list(find_module_path().values()))
        table = [(k, os.path.relpath(v, root_dir)) for k, v in find_module_path().items()]
        table.insert(0, ('', f'{os.path.relpath(__file__, root_dir)} (in {root_dir})'))
        print(tabulate.tabulate(table, headers=('Command', 'Module Path')))


an.sub_cmd = an.args = None


@apr.root()
@apr.arg(an.sub_cmd, nargs='?')
@apr.arg(an.args, nargs='*')
@apr.map(cmd_name=an.sub_cmd)
def goto_sub_cmd_module(cmd_name=None):
    if cmd_name:
        module_paths_d = find_module_path()
        if cmd_name in module_paths_d:
            module_path = module_paths_d[cmd_name]
            module = python_module_from_filepath('module', module_path)
            argv = sys.argv
            sys.argv = [f'{__stem__} {cmd_name}', *argv[2:]]
            module.main()
        else:
            print('module not found:', cmd_name, file=sys.stderr)
    else:
        meta_apr.parse()
        meta_apr.run()


def main():
    argv = sys.argv
    if len(argv) == 1:
        argv.append('-h')
    if len(argv) > 1 and argv[1] not in ('-h', '--help', '-l', '--list'):
        goto_sub_cmd_module(argv[1])
    else:
        apr.parse(catch_unknown_args=True)
        apr.run()


if __name__ == '__main__':
    main()
