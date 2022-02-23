#!/usr/bin/env python3
import tabulate

import mylib.easy
from mylib.easy import *
from mylib.easy import fstk
from ezpykit.enhance_stdlib import argparse

__dirname__, __filename_without_extension__, __file_extension__ = mylib.easy.split_path_dir_base_ext(__file__)
sub_apr = argparse.ArgumentParserRigger()
an = sub_apr.an
meta_apr = argparse.ArgumentParserRigger()


@functools.lru_cache()
def find_module_path():
    r = {}
    with fstk.ctx_pushd(__dirname__):
        for f in glob.glob(__filename_without_extension__ + '*.py*'):
            match = re.match(rf'({__filename_without_extension__})_([^.-]+)', f)
            if not match:
                continue
            name = match.group(2)
            r[name] = fstk.make_path(__dirname__, f)
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


@sub_apr.root()
@sub_apr.arg(an.sub_cmd, nargs='?')
@sub_apr.arg(an.args, nargs='*')
@sub_apr.true(an.l, an.list, help='list all sub-cmd modules')
@sub_apr.map(cmd_name=an.sub_cmd)
def goto_sub_cmd_module(cmd_name=None):
    if cmd_name:
        module_paths_d = find_module_path()
        if cmd_name in module_paths_d:
            module_path = module_paths_d[cmd_name]
            argv = sys.argv
            argv = [f'{__filename_without_extension__}{__file_extension__} {cmd_name}', *argv[2:]]
            if len(argv) < 2:
                argv.append('-h')
            sys.argv = argv
            module = python_module_from_filepath('module', module_path)
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
    if len(argv) > 1 and argv[1] not in meta_apr.option_names:
        goto_sub_cmd_module(argv[1])
    else:
        sub_apr.parse(catch_unknown_args=True)
        sub_apr.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(2)
