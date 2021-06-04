#!/usr/bin/env python3
from mylib.ex.console_app import *
import hashlib


def file_is_bad(file):
    size = path_get_size(file)
    if not size:
        return True
    if size in (14802, 8508) and hashlib.md5(open(file, 'rb').read()).hexdigest() in (
            'b325d6ba8efb828686667aa58ab549e8', 'fba5c45637db04d4797bc730c849ce30'):
        return True
    return False


def find_bad_files_iter(files):
    for fp in files:
        if file_is_bad(fp):
            yield fp


apr = ArgumentParserRigger()
an = apr.an
an.src = an.v = an.verbose = ''


@apr.sub(aliases=['rm.bad.files'])
@apr.arg(an.src, nargs='*')
@apr.true(an.v, an.verbose)
@apr.map(an.src, verbose=an.verbose, print_dirname=apr.ro(True))
def remove_expired_link_files(src, verbose=False, print_dirname=False):
    dirs, files = resolve_path_to_dirs_files(src)
    bad_files = []
    dir_with_bad_files = {}
    for path in itertools.chain(dirs, files):
        for fp in find_bad_files_iter(fstk.find_iter('f', path, recursive=True)):
            shutil.remove(fp)
            bad_files.append(fp)
            dp = path_dirname(fp)
            if dp not in dir_with_bad_files:
                dir_with_bad_files[dp] = ...
    if verbose:
        for fp in bad_files:
            print(fp)
    if print_dirname:
        ConsolePrinter().ll()
        for dp in dir_with_bad_files.keys():
            print(dp)
    return bad_files


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
