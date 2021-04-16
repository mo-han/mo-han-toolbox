#!/usr/bin/env python3
import pyperclip

from mylib.ez.ostk import *


class Clipboard(metaclass=SingletonMetaClass):
    _cb = pyperclip

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def clear(self):
        self.set('')
        return self

    def set(self, data):
        self._cb.copy(data)

    def get(self):
        return self._cb.paste()

    def list_path(self, exist_only=True):
        lines = [line.strip() for line in str(self.get()).splitlines()]
        return [line for line in lines if os.path.exists(line)]


clipboard = Clipboard()


def fs_copy_cli(src, dst):
    subprocess.run(['cp', '-r', src, dst], shell=True).check_returncode()


def fs_move_cli(src, dst):
    subprocess.run(['mv', src, dst], shell=True).check_returncode()


def set_console_title(title: str):
    print(f'\33]0;{title}\a', end='', flush=True)
