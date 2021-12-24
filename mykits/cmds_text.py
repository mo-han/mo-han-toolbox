#!/usr/bin/env python3
import difflib

from mylib.ext.console_app import *

apr = ArgumentParserRigger()
differ = difflib.Differ()
an = apr.an
an.v = an.verbose = an.r = an.recurse = an.dry_run = an.D = ''
an.text = an.s = an.src = an.find = an.replace = an.regex = an.e = an.encoding = an.c = ''


@apr.sub(aliases=['fr'])
@apr.opt(an.s, an.src, nargs='*')
@apr.true(an.r, an.recurse)
@apr.arg(an.find)
@apr.arg(an.replace, default='', nargs='?')
@apr.true(an.e, an.regex)
@apr.opt(an.c, an.encoding, default='utf-8', help='file encoding')
@apr.true(an.v, an.verbose)
@apr.true(an.D, apr.dst2opt(an.dry_run))
@apr.map(src=an.src, find=an.find, replace=an.replace, regex=an.regex, encoding=an.encoding,
         recurse=an.recurse, verbose=an.verbose, dry_run=an.dry_run)
def find_replace(src, find, replace='', encoding='utf-8', regex=False, recurse=False, verbose=False, dry_run=False):
    """find and replace text in file(s)"""
    if not regex and find == replace:
        if verbose:
            stderr_print('! `replace` is same with `find`, stopped.')
        return
    dirs, files = resolve_path_to_dirs_files(src, glob_recurse=recurse)
    for fp in files:
        with open(fp, encoding=encoding) as fd:
            old = fd.read()
        if regex:
            # if not re.search(find, old):
            #     continue
            new = re.sub(find, replace, old)
        else:
            # if find not in old:
            #     continue
            new = old.replace(find, replace)
        if old == new:
            continue
        if not dry_run:
            with open(fp, 'w', encoding=encoding) as fd:
                fd.write(new)
        if verbose:
            stderr_print(f'* {fp}')
            for line in differ.compare(old.splitlines(), new.splitlines()):
                if line[0] in ('+', '-'):
                    stderr_print(line)


@apr.sub(apr.rpl_dot())
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
