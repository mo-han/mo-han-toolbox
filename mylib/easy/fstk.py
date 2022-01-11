#!/usr/bin/env python3
import fnmatch
import html
import json
import urllib.parse
import zipfile
from enum import Enum

from mylib.easy import *
from mylib.easy import text

if os.name == 'posix':
    ILLEGAL_FS_CHARS = r'/'
    ILLEGAL_FS_CHARS_REGEX_PATTERN = re.compile(f'[{ILLEGAL_FS_CHARS}]')
    ILLEGAL_FS_CHARS_UNICODE_REPLACE = r'⧸'
    ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE = str.maketrans(ILLEGAL_FS_CHARS, ILLEGAL_FS_CHARS_UNICODE_REPLACE)
if os.name == 'nt':
    ILLEGAL_FS_CHARS = r'\/:*?"<>|'
    ILLEGAL_FS_CHARS_REGEX_PATTERN = re.compile(f'[{ILLEGAL_FS_CHARS}]')
    ILLEGAL_FS_CHARS_UNICODE_REPLACE = r'⧹⧸꞉∗？″﹤﹥￨'
    ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE = str.maketrans(ILLEGAL_FS_CHARS, ILLEGAL_FS_CHARS_UNICODE_REPLACE)

POTENTIAL_INVALID_CHARS_MAP = {
    '<': '﹤',  # U+FE64 (small less-than sign)
    '>': '﹥',  # U+FE65 (small greater-than sign)
    ':': '꞉',  # U+A789 (modifier letter colon, sometimes used in Windows filenames)
    '"': '″',  # U+2033 (DOUBLE PRIME)
    '/': '⧸',  # U+29F8 (big solidus, permitted in Windows file and folder names）
    '\\': '⧹',  # U+29F9 (big reverse solidus)
    '|': '￨',  # U+FFE8 (half-width forms light vertical)
    '?': '？',  # U+FF1F (full-width question mark)
    '*': '∗',  # U+2217 (asterisk operator)
}


def inplace_pattern_rename(src_path: str, pattern: str, repl: str, *,
                           only_basename=True, ignore_case=False, regex=False, dry_run=False
                           ) -> str or None:
    if only_basename:
        parent, basename = os.path.split(src_path)
        dst_path = os.path.join(parent,
                                text.pattern_replace(src_path, pattern, repl, regex=regex,
                                                     ignore_case=ignore_case))
    else:
        dst_path = text.pattern_replace(src_path, pattern, repl, regex=regex, ignore_case=ignore_case)
    if not dry_run:
        shutil.move(src_path, dst_path)
    if src_path != dst_path:
        return dst_path


def match_ignore_case(name: str, pattern: str):
    return bool(fnmatch.fnmatch(name, pattern))


def match(name: str, pattern: str):
    return bool(fnmatch.fnmatchcase(name, pattern))


def regex_match_ignore_case(name: str, pattern: str):
    return bool(re.search(pattern, name, flags=re.IGNORECASE))


def regex_match(name: str, pattern: str):
    return bool(re.search(pattern, name))


def factory_match_pattern(regex: bool, ignore_case: bool):
    return {
        (False, False): match, (False, True): match_ignore_case,
        (True, False): regex_match, (True, True): regex_match_ignore_case
    }[(bool(regex), bool(ignore_case))]


def find_iter(find_type: str, start_path: str = '.', pattern: str = None, *, abspath=False, recursive=True, regex=False,
              relative_to=None, ignore_case=False, include_start_dir=True, win32_unc=False):
    find_files = 'f' in find_type
    find_dirs = 'd' in find_type
    pattern = pattern or ('.*' if regex else '*')
    if win32_unc:
        start_path = make_path(start_path, win32_unc=True)
    else:
        start_path = os.path.abspath(start_path) if abspath else start_path
    if relative_to:
        def conv_path(path):
            return os.path.relpath(path, relative_to)
    else:
        def conv_path(path):
            return path
    # print(start_path)
    match_func = factory_match_pattern(regex=regex, ignore_case=ignore_case)
    basename = os.path.basename
    if os.path.isfile(start_path):
        if find_files and match_func(basename(start_path), pattern):
            yield conv_path(start_path)
        return
    if os.path.isdir(start_path):
        if find_dirs and match_func(basename(start_path), pattern) and include_start_dir:
            yield conv_path(start_path)
        if not recursive:
            return
    # p,d,f = dirpath, dirnames, filenames
    # n = name = dirname/filename from dirnames/filenames
    walk_pdf = ((p, d, f) for p, d, f in (os.walk(start_path)))
    if find_files and find_dirs:
        chain_iter = itertools.chain
        yield from (conv_path(os.path.join(p, n)) for p, d, f in walk_pdf for n in chain_iter(d, f) if
                    match_func(n, pattern))
    elif find_files:
        yield from (conv_path(os.path.join(p, n)) for p, d, f in walk_pdf for n in f if match_func(n, pattern))
    elif find_dirs:
        yield from (conv_path(os.path.join(p, n)) for p, d, f in walk_pdf for n in d if match_func(n, pattern))
    else:
        return


def files_from_iter(src: str or T.Iterable, *, recursive=False, win32_unc=False):
    def mkp(*parts):
        return make_path(*parts, win32_unc=win32_unc)

    if isinstance(src, str):
        if os.path.isfile(src):
            yield mkp(src)
        elif os.path.isdir(src):
            if recursive:
                yield from find_iter('f', src, recursive=True, win32_unc=win32_unc)
            else:
                for fn in next(os.walk(src))[-1]:
                    yield mkp(src, fn)
        else:
            for p in glob.glob(src, recursive=recursive):
                if os.path.isfile(p):
                    yield p
    else:
        for s in src:
            yield from files_from_iter(s, recursive=recursive, win32_unc=win32_unc)


def make_path(*parts, absolute=False, follow_link=False, relative_to: str = None,
              user_home=False, env_var=False, win32_unc=False, part_converter=None):
    if part_converter:
        parts = [part_converter(part) for part in parts]
    if win32_unc:
        absolute = True
    if absolute and relative_to:
        raise ValueError('both `absolute` and `relative` are enabled')
    path = os.path.join(*parts)
    if follow_link:
        path = os.path.realpath(path)
    if absolute:
        path = os.path.abspath(path)
    elif relative_to is not None:
        path = os.path.relpath(path, relative_to)
    if user_home:
        path = os.path.expanduser(path)
    if env_var:
        path = os.path.expandvars(path)
    if win32_unc:
        if not path.startswith('\\\\?\\'):
            path = rf'\\?\{path}'
    return path


def read_json_file(file, default=None, utf8: bool = True, **kwargs) -> dict:
    file_kwargs = {}
    if utf8:
        file_kwargs['encoding'] = 'utf8'
    with ensure_open_file(file, 'r', **file_kwargs) as jf:
        try:
            d = json.load(jf, **kwargs)
        except json.decoder.JSONDecodeError:
            d = default or {}
    return d


def write_json_file(file, data, *, indent=None, utf8: bool = True, **kwargs):
    file_kwargs = {}
    if utf8:
        file_kwargs['encoding'] = 'utf8'
    with ensure_open_file(file, 'w', **file_kwargs) as jf:
        json.dump(data, jf, indent=indent, ensure_ascii=not utf8, **kwargs)


def touch(filepath):
    try:
        os.utime(filepath)
    except OSError:
        open(filepath, 'a').close()


def x_rename(src_path: str, dst_name_or_path: str = None, dst_ext: str = None, *,
             move_to_dir: str = None, stay_in_src_dir: bool = True, append_src_ext: bool = True) -> str:
    src_root, src_basename = os.path.split(src_path)
    src_before_ext, src_ext = os.path.splitext(src_basename)
    if dst_ext is not None:
        if dst_name_or_path is None:
            dst_name_or_path = src_before_ext + dst_ext
        else:
            dst_name_or_path += dst_ext
    if move_to_dir:
        dst_path = os.path.join(move_to_dir, dst_name_or_path)
    elif stay_in_src_dir:
        dst_path = os.path.join(src_root, dst_name_or_path)
    else:
        dst_path = dst_name_or_path
    if append_src_ext:
        dst_path = dst_path + src_ext
    return shutil.move(src_path, dst_path)


def sanitize(name: str, repl: str or dict = None, *, unescape_html=True, decode_url=True) -> str:
    if unescape_html:
        name = html.unescape(name)
    if decode_url:
        name = urllib.parse.unquote(name)
    if repl:
        if isinstance(repl, str):
            r = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, name)
            # rl = len(repl)
            # if rl > 1:
            #     r = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            # elif rl == 1:
            #     r = x.translate(str.maketrans(ILLEGAL_FS_CHARS, repl * ILLEGAL_FS_CHARS_LEN))
            # else:
            #     r = x.translate(str.maketrans('', '', ILLEGAL_FS_CHARS))
        elif isinstance(repl, dict):
            r = name.translate(str.maketrans(repl))
        else:
            raise TypeError('invalid repl', (str, dict), repl)
    else:
        r = name.translate(ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE)
    return r


def sanitize_xu(name: str, *, reverse=False, unescape_html=True, decode_url=True, unify_white_space=True) -> str:
    chars_map = POTENTIAL_INVALID_CHARS_MAP
    if reverse:
        chars_map = dict(zip(chars_map.values(), chars_map.keys()))
    r = sanitize(name, chars_map, unescape_html=unescape_html, decode_url=decode_url)
    if unify_white_space:
        r = re.sub(r'\s', ' ', r)
    return r


def sanitize_xu200(name: str, encoding: str = 'utf8') -> str:
    return text.ellipt_end(sanitize_xu(name), 200, encoding=encoding)


def sanitize_xu240(name: str, encoding: str = 'utf8') -> str:
    return text.ellipt_end(sanitize_xu(name), 240, encoding=encoding)


def sanitize_xu_left(name: str, limit: int, encoding: str = 'utf8') -> str:
    return text.ellipt_end(sanitize_xu(name), limit, encoding=encoding)


def ensure_open_file(filepath, mode='r', **kwargs):
    parent, basename = os.path.split(filepath)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    if not os.path.isfile(filepath):
        try:
            open(filepath, 'a').close()
        except PermissionError as e:
            if os.path.isdir(filepath):
                raise FileExistsError("path used by directory '{}'".format(filepath))
            else:
                raise e
    return open(filepath, mode, **kwargs)


@contextlib.contextmanager
def ctx_pushd(dst: str, ensure_dst: bool = False):
    if dst == '':
        yield
        return
    if ensure_dst:
        cd = ensure_chdir
    else:
        cd = os.chdir
    prev = os.getcwd()
    saved_error = None
    try:
        cd(dst)
        yield
    except Exception as e:
        saved_error = e
    finally:
        cd(prev)
        if saved_error:
            raise saved_error


def ensure_chdir(dest: str):
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    os.chdir(dest)


def path_or_glob(pathname, *, recursive=False):
    if os.path.exists(pathname):
        return [pathname]
    else:
        return glob.glob(pathname, recursive=recursive)


def path_parts(path):
    pp = pathlib.Path(path)
    return pp.parts


def make_zipfile_from_dir(zip_path, src_dir, *, strip_src_dir=True, **zipfile_kwargs):
    src_dir_path = pathlib.Path(src_dir)
    if not os.path.isdir(src_dir_path):
        raise NotADirectoryError(src_dir)
    with zipfile.ZipFile(zip_path, 'w', **zipfile_kwargs) as zf:
        for file in src_dir_path.rglob('*'):
            zf.write(file, file.relative_to(src_dir_path if strip_src_dir else src_dir_path.parent))


class FileSystemError(Exception):
    pass


class FileToDirError(FileSystemError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class DirToFileError(FileSystemError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class NotFileNotDirError(FileSystemError):
    pass


class NotExistError(FileSystemError):
    pass


class AlreadyExistError(FileSystemError):
    pass


class OnExist(Enum):
    ERROR = 'error'
    OVERWRITE = 'overwrite'
    RENAME = 'rename'


def wrapped_shutil_move(src, dst):
    try:
        return shutil.move(src, dst)
    except shutil.Error as e:
        if e.args:
            msg = e.args[0]
            m = re.match(r"Destination path '(.+)' already exists", msg)
            if m:
                raise AlreadyExistError(m.group(1))
            else:
                raise
        else:
            raise


def index_if_path_exist(target_path):
    without_ext, extension = path_split_ext(path_normalize(target_path))
    dup_count = 1
    while path_exist(target_path):
        target_path = f'{without_ext} ({dup_count}){extension}'
        dup_count += 1
    else:
        return target_path


def move_as(src, dst, *, on_exist: OnExist = OnExist.OVERWRITE, dry_run=False, predicate_path_use_cache=False):
    """move strictly from src to dst, if dst is dir, move to it instead of into it"""
    if not isinstance(on_exist, OnExist):
        raise TypeError('on_exist', OnExist)
    if not path_exist(src):
        raise NotExistError(src)

    if not path_exist(dst):
        if dry_run:
            return dst
        else:
            dst_dir = path_dirname(path_normalize(dst))
            if dst_dir:
                os.makedirs(dst_dir, exist_ok=True)
            return wrapped_shutil_move(src, dst)

    if predicate_fs_path('d', src, use_cache=predicate_path_use_cache):
        if predicate_fs_path('d', dst, use_cache=predicate_path_use_cache):
            if dry_run:
                return dst
            for src_root_dir, src_sub_dirs, src_sub_files in os.walk(src):
                root_dir_relative_in_src = path_relative(src_root_dir, src)
                if root_dir_relative_in_src == '.':
                    root_dir_relative_in_dst = dst
                else:
                    root_dir_relative_in_dst = path_join(dst, root_dir_relative_in_src)
                os.makedirs(root_dir_relative_in_dst, exist_ok=True)
                for f in src_sub_files:
                    sub_src = path_join(src_root_dir, f)
                    sub_dst = path_join(root_dir_relative_in_dst, f)
                    if not path_exist(sub_dst):
                        wrapped_shutil_move(sub_src, sub_dst)
                        continue
                    if predicate_fs_path('d', sub_dst, use_cache=predicate_path_use_cache):
                        if on_exist == OnExist.RENAME:
                            wrapped_shutil_move(sub_src, index_if_path_exist(sub_dst))
                            continue
                        if on_exist == OnExist.OVERWRITE:
                            raise FileToDirError(sub_src, sub_dst)
                        if on_exist == OnExist.ERROR:
                            raise AlreadyExistError(sub_dst)
                    if on_exist == OnExist.OVERWRITE:
                        wrapped_shutil_move(sub_src, sub_dst)
                        continue
                    if on_exist == OnExist.RENAME:
                        wrapped_shutil_move(sub_src, index_if_path_exist(sub_dst))
                        continue
                    if on_exist == OnExist.ERROR:
                        raise AlreadyExistError(sub_dst)
            shutil.rmtree(src)
            return dst
        raise DirToFileError(src, dst)

    if on_exist == OnExist.RENAME:
        new_dst = index_if_path_exist(dst)
        if dry_run:
            return new_dst
        else:
            os.makedirs(path_dirname(new_dst))
            return wrapped_shutil_move(src, new_dst)
    if predicate_fs_path('d', dst, use_cache=predicate_path_use_cache):
        raise FileToDirError(src, dst)
    if on_exist == OnExist.OVERWRITE:
        return dst if dry_run else wrapped_shutil_move(src, dst)
    if on_exist == OnExist.ERROR:
        raise AlreadyExistError(dst)
    raise RuntimeError('unknown situation')


def regex_rename_basename(src_path, pattern, replace, *, ignore_ext=False, on_exist=OnExist.ERROR, dry_run=False):
    dirname, basename = os.path.split(src_path)
    to_rename, ext = (basename, '') if ignore_ext else os.path.splitext(basename)
    renamed = re.sub(pattern, replace, to_rename)
    if renamed == to_rename:
        return None
    new = join_path_dir_base_ext(dirname, renamed, ext)
    if not dry_run:
        os.makedirs(os.path.dirname(new), exist_ok=True)
    return move_as(src_path, new, on_exist=on_exist, dry_run=dry_run)


def rename_file_ext(fp, new_ext: str):
    prefix, ext = path_split_ext(fp)
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    new = prefix + new_ext
    os.rename(fp, new)
    return new
