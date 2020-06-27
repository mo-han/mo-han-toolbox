#!/usr/bin/env python3
# encoding=utf8
import os
import re
import shutil

import PySimpleGUIQt as PySimpleGUI

from .tricks import remove_from_iterable, dedup_iterable
from .util import ensure_sigint_signal, real_join_path, write_json_file, read_json_file

SPECIAL_KEYS = {
    'special 16777216': 'esc',
    'special 16777249': 'ctrl',
    'special 16777248': 'shift',
    'special 16777250': 'win',
    'special 16777301': 'menu',
    'special 16777217': 'tab',
    'special 16777251': 'alt',
    'special 16777223': 'delete',
    'special 16777232': 'home',
    'special 16777233': 'end',
    'special 16777238': 'pageup',
    'special 16777239': 'pagedown',
    'special 16777222': 'insert',
    'special 16777253': 'numlock',
    'special 16777220': 'enter',
    'special 16777219': 'backspace',
    'special 16777235': 'up',
    'special 16777237': 'down',
    'special 16777234': 'left',
    'special 16777236': 'right',
}


def rename_dialog(src: str):
    sg = PySimpleGUI
    conf_file = real_join_path('~', '.config/rename_dialog.json')
    root = 'root'
    fname = 'fname'
    ext = 'ext'
    new_root = 'new_root'
    new_base = 'new_base'
    ok = 'OK ↩'
    esc = 'Esc'
    patt = 'pattern'
    add_regex = 'add'
    del_regex = 'del'
    repl = 'replace'
    title = 'Rename - {}'.format(src)
    h = .7
    error = 'error'

    conf_dict = read_json_file(conf_file, default={patt: [''], repl: ['']})
    pattern_l = conf_dict[patt]
    replace_l = conf_dict[repl]
    old_root, old_base = os.path.split(src)
    old_fn, old_ext = os.path.splitext(old_base)

    # import random
    # sg.theme(random.choice(sg.theme_list()))
    layout = [
        [sg.T(src, key='src')],
        [sg.HorizontalSeparator()],
        [sg.I(old_root, key=root),
         sg.FolderBrowse('...', target=root, initial_folder=old_root, size=(6, h))],
        [sg.I(old_fn, key=fname, focus=True),
         sg.I(old_ext, key=ext, size=(6, h))],
        [sg.HorizontalSeparator()],
        [sg.T('Regular Expression Substitution', size=(32, h)), ],
        [sg.T('Pattern:', size=(5, h)),
         sg.Drop(pattern_l, default_value=pattern_l[0], key=patt, enable_events=True)],
        [sg.T('Replace:', size=(5, h)),
         sg.Drop(replace_l, default_value=pattern_l[0], key=repl, enable_events=True)],
        [sg.T(''), sg.B('+', key=add_regex, size=(3, h)), sg.B('-', key=del_regex, size=(3, h)), sg.T('')],
        [sg.HorizontalSeparator()],
        [sg.I(old_root, key=new_root)],
        [sg.I(old_fn + old_ext, key=new_base)],
        [sg.Submit(ok, size=(10, 1)),
         # sg.T('', key=error, font=(None, None, 'bold'), text_color='red'),
         sg.Stretch(),
         sg.Cancel(esc, size=(10, 1))]]

    ensure_sigint_signal()
    window = sg.Window(title, return_keyboard_events=True).layout(layout).finalize()
    window.bring_to_front()

    def update_regex(pl, rl):
        pl = dedup_iterable(pl)
        rl = dedup_iterable(rl)
        window[patt].update(values=pl)
        window[repl].update(values=rl)
        conf_dict[patt] = pl
        conf_dict[repl] = rl
        write_json_file(conf_file, conf_dict, indent=0)
        return pl, rl

    loop = True
    data = {fname: old_fn, ext: old_ext, patt: pattern_l[0], repl: replace_l[0], root: old_root}
    while loop:
        try:
            tmp_fname = data[fname] + data[ext]
            if data[patt]:
                # noinspection PyBroadException
                try:
                    tmp_fname = re.sub(data[patt], data[repl], tmp_fname)
                except Exception:
                    pass
            dst = os.path.realpath(os.path.join(data[root], tmp_fname))
        except TypeError:
            dst = src
        np, nb = os.path.split(dst)
        window[new_root].update(np)
        window[new_base].update(nb)

        event, data = window.read()
        window[new_root].update(text_color=None)
        window[new_base].update(text_color=None)
        cur_p = data[patt]
        cur_r = data[repl]

        if event == add_regex:
            pattern_l.insert(0, cur_p)
            replace_l.insert(0, cur_r)
            pattern_l, replace_l = update_regex(pattern_l, replace_l)
        elif event == del_regex:
            if cur_p:
                pattern_l = remove_from_iterable(pattern_l, [cur_p])
            if cur_r:
                replace_l = remove_from_iterable(replace_l, [cur_r])
            pattern_l, replace_l = update_regex(pattern_l, replace_l)
        elif event in (None, esc):
            loop = False
        elif event == ok:
            try:
                shutil.move(src, dst)
                loop = False
            except (FileNotFoundError, FileExistsError) as e:
                window[new_root].update(text_color='red')
                window[new_base].update(text_color='red')
        elif event in SPECIAL_KEYS and SPECIAL_KEYS[event] == 'esc':
            loop = False

    window.close()
