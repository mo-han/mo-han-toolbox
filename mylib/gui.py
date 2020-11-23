#!/usr/bin/env python3
# encoding=utf8
import os
import re
import shutil
from collections import defaultdict

from .tricks_base import deco_factory_retry, singleton, remove_from_list, dedup_list
from .osutil_base import ensure_sigint_signal
from ._deprecated import real_join_path
from .fsutil import read_json_file, write_json_file


@singleton
class PySimpleGUISpecialKeyEvent:
    key_event_mapping = defaultdict(lambda: None, {
        'alt': 'special 16777251',
        'backspace': 'special 16777219',
        'ctrl': 'special 16777249',
        'delete': 'special 16777223',
        'down': 'special 16777237',
        'end': 'special 16777233',
        'enter': 'special 16777220',
        'esc': 'special 16777216',
        'home': 'special 16777232',
        'insert': 'special 16777222',
        'left': 'special 16777234',
        'menu': 'special 16777301',
        'numlock': 'special 16777253',
        'pagedown': 'special 16777239',
        'pageup': 'special 16777238',
        'right': 'special 16777236',
        'shift': 'special 16777248',
        'tab': 'special 16777217',
        'up': 'special 16777235',
        'win': 'special 16777250'
    })

    def __getitem__(self, item):
        return self.key_event_mapping[item]

    def __getattr__(self, item):
        return self.key_event_mapping[item]


def rename_dialog(src: str):
    import PySimpleGUIQt
    sg = PySimpleGUIQt
    ske = PySimpleGUISpecialKeyEvent()
    conf_file = real_join_path('~', '.config/rename_dialog.json')
    root = 'root'
    fname = 'fname'
    ext = 'ext'
    new_root = 'new_root'
    new_base = 'new_base'
    ok = 'OK'
    cancel = 'Cancel'
    pattern = 'pattern'
    replace = 'replace'
    substitute = 'substitute'
    save_replace = 'save_replace'
    save_pattern = 'save_pattern'
    add_root = 'add_root'
    rename_info_file = 'rename_info_file'
    title = 'Rename - {}'.format(src)
    h = .7

    conf = read_json_file(conf_file, default={pattern: [''], replace: ['']})
    tmp_pl = conf[pattern] or ['']
    tmp_rl = conf[replace] or ['']
    old_root, old_base = os.path.split(src)
    old_fn, old_ext = os.path.splitext(old_base)
    info_file_base = [f for f in os.listdir(old_root) if
                      f.endswith('.info') and (f.startswith(old_fn) or old_fn.startswith(f.rstrip('.info')))]
    has_info = True if info_file_base else False

    # sg.theme('SystemDefaultForReal')
    layout = [
        [sg.T(src, key='src')],
        [sg.HorizontalSeparator()],
        [sg.I(old_fn, key=fname, focus=True),
         sg.I(old_ext, key=ext, size=(6, h))],
        [sg.I(old_root, key=root),
         sg.B('+', key=add_root, size=(3, h)),
         sg.FolderBrowse('...', target=root, initial_folder=old_root, size=(6, h))],
        [sg.HorizontalSeparator()],
        [sg.T('Regular Expression Substitution Pattern & Replacement')],
        [sg.T(size=(0, h)),
         sg.Drop(tmp_pl, key=pattern, enable_events=True, text_color='blue'),
         sg.CB('', default=True, key=save_pattern, enable_events=True, size=(2, h)),
         sg.Drop(tmp_rl, key=replace, enable_events=True, text_color='blue'),
         sg.CB('', default=True, key=save_replace, enable_events=True, size=(2, h)),
         sg.B('Go', key=substitute, size=(3, h))],
        [sg.HorizontalSeparator()],
        [sg.I(old_root, key=new_root)],
        [sg.I(old_fn + old_ext, key=new_base)],
        [sg.Submit(ok, size=(10, 1)),
         sg.Stretch(),
         sg.Cancel(cancel, size=(10, 1))]]
    if has_info:
        info_file_base = info_file_base[0]
        info_filepath = os.path.join(old_root, info_file_base)
        with open(info_filepath, encoding='utf8') as f:
            info = f.read()
        layout.insert(2, [sg.CB(info_file_base, default=True, key=rename_info_file, enable_events=True)])
        layout.insert(2, [sg.ML(info)])
        layout.insert(4, [sg.HorizontalSeparator()])

    ensure_sigint_signal()
    window = sg.Window(title, return_keyboard_events=True).layout(layout).finalize()
    window.bring_to_front()

    loop = True
    data = {fname: old_fn, ext: old_ext, pattern: tmp_pl[0], replace: tmp_rl[0], root: old_root,
            new_root: '', new_base: ''}

    @deco_factory_retry(Exception, 0, enable_default=True, default=None)
    def re_sub():
        return re.sub(data[pattern], data[replace], data[fname] + data[ext])

    while loop:
        dst_from_data = os.path.join(data[new_root], data[new_base])
        try:
            tmp_fname = re_sub() or data[fname] + data[ext]
            dst = os.path.realpath(os.path.join(data[root], tmp_fname))
        except TypeError:
            dst = src
        if dst != dst_from_data:
            nr, nb = os.path.split(dst)
            window[new_root].update(nr)
            window[new_base].update(nb)

        event, data = window.read()
        f = window.find_element_with_focus()
        for k in (root, fname, ext, new_root, new_base):
            window[k].update(text_color=None)
        cur_p = data[pattern]
        cur_r = data[replace]

        if event == ske.esc:
            loop = False
        elif event == add_root:
            os.makedirs(data[root], exist_ok=True)
        elif event == substitute:
            data[fname], data[ext] = os.path.splitext(re_sub() or data[fname] + data[ext])
            window[fname].update(data[fname])
            window[ext].update(data[ext])
        elif event == save_pattern:
            if data[save_pattern]:
                conf[pattern].insert(0, cur_p)
                conf[pattern] = dedup_list(conf[pattern])
            else:
                conf[pattern] = remove_from_list(conf[pattern], [cur_p])
        elif event == save_replace:
            if data[save_replace]:
                conf[replace].insert(0, cur_r)
                conf[replace] = dedup_list(conf[replace])
            else:
                conf[replace] = remove_from_list(conf[replace], [cur_r])
        elif event == pattern:
            window[save_pattern].update(value=cur_p in conf[pattern])
        elif event == replace:
            window[save_replace].update(value=cur_r in conf[replace])
        elif event == ok:
            try:
                shutil.move(src, dst)
                if has_info:
                    if data[rename_info_file]:
                        shutil.move(info_filepath,
                                    os.path.splitext(dst)[0] + '.info')
                loop = False
            except FileNotFoundError:
                for k in (root, fname, ext):
                    window[k].update(text_color='red')
            except FileExistsError:
                for k in (new_root, new_base):
                    window[k].update(text_color='red')
            except OSError as e:
                sg.PopupError(str(e))
        elif event in (None, cancel):
            loop = False
        else:
            ...
    else:
        write_json_file(conf_file, conf, indent=0)

    window.close()
