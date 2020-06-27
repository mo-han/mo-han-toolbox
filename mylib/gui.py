#!/usr/bin/env python3
# encoding=utf8
import os
import shutil

import PySimpleGUIQt as PySimpleGUI

from .osutil import ensure_sigint_signal, real_join_path

SPECIAL_KEYS = {
    'special 16777216': 'esc',
    'special 16777249': 'ctrl',
    'special 16777248': 'shift',
    'special 16777250': 'win',
    'special 16777301': 'apps',
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
    conf_file = real_join_path(os.path.expanduser('~'), '.config/rename_dialog_conf.json')
    root = 'root'
    fname = 'fname'
    ext = 'ext'
    new = 'new'
    ok = 'OK ↩'
    discard = 'Esc'
    title = 'Rename - {}'.format(src)
    h = .7

    old_root, old_base = os.path.split(src)
    old_fn, old_ext = os.path.splitext(old_base)

    # sg.theme(random.choice(sg.theme_list()))
    layout = [
        [sg.T(src, key='src')],
        [sg.HorizontalSeparator()],
        [
            sg.I(default_text=old_root, key=root),
            sg.FolderBrowse(button_text='...', target=root, initial_folder=old_root, size=(6, h))
        ],
        [
            sg.I(default_text=old_fn, key=fname, focus=True),
            sg.I(default_text=old_ext, key=ext, size=(6, h))
        ],
        [sg.Combo(['1', '2'])],
        [sg.HorizontalSeparator()],
        [sg.MultilineOutput(src, key=new)],
        [
            sg.Submit(button_text=ok, size=(10, 1)),
            sg.Stretch(),
            sg.Cancel(button_text=discard, size=(10, 1))]
    ]

    ensure_sigint_signal()
    window = sg.Window(title, return_keyboard_events=True, ).layout(layout).finalize()
    window.bring_to_front()
    while True:
        e, d = window.read()
        try:
            dst = os.path.realpath(os.path.join(d[root], d[fname] + d[ext]))
        except TypeError:
            dst = src
        window.find_element(new).update(dst)
        if e in (None, discard):
            break
        elif e == ok:
            shutil.move(src, dst)
            break
        elif e in SPECIAL_KEYS and SPECIAL_KEYS[e] == 'esc':
            break
    window.close()
