#!/usr/bin/env python3
import difflib

from mylib.ex.console_app import *

apr = ArgumentParserRigger()
an = apr.an

an.text = ''


@apr.sub()
@apr.arg(an.text, nargs='?')
@apr.map(an.text)
def obsidian_reformat(s: str):
    old = s or ostk.clipboard.get()
    new = re.sub(r'\[(\[.+])](\(.+\))', r'[ \1 ]\2', old)
    ostk.clipboard.clear()
    ostk.clipboard.set(new)
    if new != old:
        for line in difflib.Differ().compare(old.splitlines(), new.splitlines()):
            if line[0] in ('+', '-'):
                print(line, file=sys.stderr)
    return new


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
