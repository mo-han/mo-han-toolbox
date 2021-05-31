#!/usr/bin/env python3
import PIL.Image
import pywintypes
import win32clipboard
import psutil

from mylib.easy.ostk import *


class Clipboard(metaclass=SingletonMetaClass):
    _wcb = win32clipboard
    cf_dict = {str_remove_prefix(name, 'CF_'): method for name, method in inspect.getmembers(_wcb) if
               name.startswith('CF_')}

    class OpenError(Exception):
        pass

    def __init__(self):
        self.delay = 0
        try:
            self._wcb.CloseClipboard()
        except pywintypes.error:
            pass
        finally:
            self.__opened = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def is_opened(self):
        return self.__opened

    @property
    def is_closed(self):
        return not self.__opened

    def open(self):
        if not self.__opened:
            sleep(self.delay)
            try:
                self._wcb.OpenClipboard()
                self.__opened = True
            except pywintypes.error:
                raise self.OpenError

    def close(self):
        if self.__opened:
            self._wcb.CloseClipboard()
            # sleep(self.delay)  # maybe not needed
            self.__opened = False

    def valid_format(self, x: str or int):
        """get valid clipboard format ('CF_*')"""
        if isinstance(x, int):
            pass
        elif isinstance(x, str):
            x = x.upper()
            if not x.startswith('x_'):
                x = 'CF_' + x
            x = getattr(self._wcb, x)
        else:
            raise TypeError("'{}' is not str or int".format(x))
        return x

    @tricks.deco_with_self_context
    def clear(self):
        self._wcb.EmptyClipboard()
        return self

    @tricks.deco_with_self_context
    def set(self, data, cf=_wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        return self._wcb.SetClipboardData(cf, data)

    @tricks.deco_with_self_context
    def set_text___fixme(self, text):
        return self._wcb.SetClipboardText(text)

    @tricks.deco_with_self_context
    def get(self, cf=_wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        if self._wcb.IsClipboardFormatAvailable(cf):
            data = self._wcb.GetClipboardData(cf)
        else:
            data = None
        return data

    @tricks.deco_with_self_context
    def set_image(self, image):
        if isinstance(image, str):
            if re.match(r'data:image/\w+;base64, [A-Za-z0-9+/=]+', image):
                raise NotImplementedError('base64 image data')
            else:
                i = PIL.Image.open(image)
                with io.BytesIO() as o:
                    i.convert('RGB').save(o, 'BMP')
                    data = o.getvalue()[14:]  # https://stackoverflow.com/questions/34322132/copy-image-to-clipboard
        elif isinstance(image, PIL.Image.Image):
            with io.BytesIO() as o:
                image.convert('RGB').save(o, 'BMP')
                data = o.getvalue()[14:]
        elif isinstance(image, bytes):
            data = image
        else:
            raise TypeError('image', (str, PIL.Image.Image, bytes), type(image))
        self.set(data, self._wcb.CF_DIB)

    def list_path(self, exist_only=True) -> list:
        paths = self.get(self._wcb.CF_HDROP)
        if paths:
            if exist_only:
                return [p for p in paths if os.path.exists(p)]
            else:
                return list(paths)
        else:
            lines = [line.strip() for line in str(self.get()).splitlines()]
            return [line for line in lines if os.path.exists(line)]

    @tricks.deco_with_self_context
    def get_all(self) -> dict:
        d = {}
        for k, v in self.cf_dict.items():
            if self._wcb.IsClipboardFormatAvailable(v):
                d[k] = self._wcb.GetClipboardData(v)
        return d


clipboard = Clipboard()


def fs_copy_cli(src, dst):
    subprocess.run(['copy', src, dst], shell=True).check_returncode()


def _fs_move_cli_move(src, dst):
    subprocess.run(['move', src, dst], shell=True).check_returncode()


def _fs_move_cli_robocopy(src, dst, quiet=True, verbose=False):
    full_log = verbose or not quiet
    args = ['robocopy']
    if not full_log:
        # https://stackoverflow.com/a/7487697/7966259
        # /NFL : No File List - don't log file names.
        # /NDL : No Directory List - don't log directory names.
        # /NJH : No Job Header.
        # /NJS : No Job Summary.
        # /NP  : No Progress - don't display percentage copied.
        # /NS  : No Size - don't log file sizes.
        # /NC  : No Class - don't log file classes.
        args.extend(['/NJH', '/NJS', '/NFL', '/NDL'])
    if os.path.isdir(src):
        args.extend(['/E', '/IS'])
    args.extend(['/MOVE', src, dst])
    proc = subprocess.run(args, shell=True)
    if proc.returncode > 1:
        raise subprocess.CalledProcessError(proc.returncode, args, proc.stdout, proc.stderr)


def fs_move_cli(src, dst, quiet=True, verbose=False):
    if os.path.isfile(src):
        _fs_move_cli_move(src, dst)
    elif os.path.isdir(src):
        _fs_move_cli_robocopy(src, dst, quiet=quiet, verbose=verbose)
    else:
        raise ValueError(src)


def set_console_title(title: str, *, shell=True, escape=True):
    if shell:
        if escape:
            title = re.sub(r'([&<>^%])', '^\1', title)
        os.system(f'title {title}')
    else:
        # https://stackoverflow.com/a/12626424/7966259
        ctypes.windll.kernel32.SetConsoleTitleW(title)


def deco_factory_daemon_subprocess(*, flag_env_var_name='__this_daemon_subprocess__', **kwargs_for_subprocess):
    def deco(target):
        @functools.wraps(target)
        def tgt(*args, **kwargs):
            if os.environ.get(flag_env_var_name) == __file__:
                target(*args, **kwargs)
            else:
                os.environ[flag_env_var_name] = __file__
                real_argv = psutil.Process(os.getpid()).cmdline()
                exec_dir, exec_basename = path_split(real_argv[0])
                if exec_basename.lower() == 'python.exe':
                    real_argv[0] = shutil.which('pythonw.exe')
                kwargs = dict(env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
                kwargs.update(kwargs_for_subprocess)
                subprocess.Popen(real_argv, **kwargs)

        return tgt

    return deco
