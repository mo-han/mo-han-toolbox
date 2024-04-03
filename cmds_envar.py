#!/usr/bin/env python3
from oldezpykitext.appkit import *
from oldezpykitext.yaml import EzYAML

ap = argparse.ArgumentParserWrapper()
an = ap.an


def main():
    ap.parse()
    ap.run()


@ap.sub('setuv')
@ap.arg('entry', nargs='*', help='name=value')
@ap.opt('f', 'file', nargs='*')
@ap.map('entry', files='file')
def set_user_vars(entries=None, files=None):
    # print(entries, files)
    entries = entries or []
    files = files or []
    envars = {}
    for e in entries:
        k, v = e.split('=', maxsplit=1)
        envars[str(k)] = str(v)
    # print(envars)
    for fp in files:
        y = EzYAML().set_file(fp).load()
        for x in y.documents:
            if isinstance(x, dict):
                for k, v in x.items():
                    envars[str(k)] = str(v)
            else:
                continue
    # print(envars)
    os.EnVarKit.save(envars)
    # print(envars)
    for k, v in envars.items():
        print(f'{k}={v}')


if __name__ == '__main__':
    main()
