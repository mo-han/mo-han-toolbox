#!/usr/bin/env python3
# encoding=utf8
import os
import re
import shutil
from collections import defaultdict

from .ex.tricks import deco_factory_retry, singleton, remove_from_list
from .easy import dedup_list
from mylib.easy.ostk import ensure_sigint_signal
from .__deprecated__ import real_join_path
from mylib.ex.fstk import read_json_file, write_json_file
from mylib.ex.text import encode_default_locale


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
    import PySimpleGUIQt as G
    ske = PySimpleGUISpecialKeyEvent()
    conf_file = real_join_path('~', '.config/rename_dialog.json')
    root = 'root'
    fname = 'fname'
    ext = 'ext'
    key_new_root = 'key_new_root'
    key_new_base = 'key_new_base'
    ok = 'OK'
    cancel = 'Cancel'
    pattern = 'pattern'
    replace = 'replace'
    substitute = 'substitute'
    save_replace = 'save_replace'
    save_pattern = 'save_pattern'
    add_root = 'add_root'
    rename_info_file = 'rename_info_file'
    bytes_count = 'bytes_count'
    title = 'Rename - {}'.format(src)
    h = None

    conf = read_json_file(conf_file, default={pattern: [''], replace: ['']})
    tmp_pl = conf[pattern] or ['']
    tmp_rl = conf[replace] or ['']
    old_root, old_base = os.path.split(src)
    old_fn, old_ext = os.path.splitext(old_base)
    info_file_base = [f for f in os.listdir(old_root) if
                      f.endswith('.info') and (f.startswith(old_fn) or old_fn.startswith(f.rstrip('.info')))]
    has_info = True if info_file_base else False

    @deco_factory_retry(Exception, 0, enable_default=True, default=None)
    def re_sub():
        return re.sub(data[pattern], data[replace], data[fname] + data[ext])

    def count_name_bytes(name: str):
        d = {}
        try:
            c, b = encode_default_locale(name)
            d[c] = len(b)
        except UnicodeEncodeError:
            pass
        u8 = 'utf-8'
        if u8 not in d:
            try:
                c, b = encode_default_locale(name, u8)
                d[c] = len(b)
            except UnicodeEncodeError:
                pass
        return f'Basename Length: {len(name)}, {", ".join([f"{k.upper()} {v} bytes" for k, v in d.items()])}'

    # sg.theme('SystemDefaultForReal')
    layout = [
        [G.T(src, key='src')],
        [G.HorizontalSeparator()],
        [G.I(old_fn, key=fname, focus=True),
         G.I(old_ext, key=ext, size=(42, h))],
        [G.I(old_root, key=root),
         G.B('+', key=add_root, size=(20, h)),
         G.FolderBrowse('...', target=root, initial_folder=old_root, size=(20, h))],
        [G.HorizontalSeparator()],
        [G.T('Regular Expression Pattern & Replacement')],
        [G.T(size=(0, h)),
         G.Drop(tmp_pl, key=pattern, enable_events=True, text_color='blue'),
         G.CB('', default=True, key=save_pattern, enable_events=True, size=(15, h)),
         G.Drop(tmp_rl, key=replace, enable_events=True, text_color='blue'),
         G.CB('', default=True, key=save_replace, enable_events=True, size=(15, h)),
         G.B('Go', key=substitute, size=(25, h))],
        [G.HorizontalSeparator()],
        [G.I(old_root, key=key_new_root)],
        [G.I(old_base, key=key_new_base)],
        [G.Submit(ok, size=(10, 1)),
         G.Stretch(), G.T(count_name_bytes(old_base), key=bytes_count), G.Stretch(),
         G.Cancel(cancel, size=(10, 1))]]
    if has_info:
        info_file_base = info_file_base[0]
        info_filepath = os.path.join(old_root, info_file_base)
        with open(info_filepath, encoding='utf8') as f:
            info = f.read()
        layout.insert(2, [G.CB(info_file_base, default=True, key=rename_info_file, enable_events=True)])
        layout.insert(2, [G.ML(info, key='ML')])
        layout.insert(4, [G.HorizontalSeparator()])

    ensure_sigint_signal()
    window = G.Window(title, layout, return_keyboard_events=True, finalize=True, font='arial 10',
                      element_padding=(1, 1))
    window.bring_to_front()
    ml = window.find_element('ML', silent_on_error=True)
    if ml:
        ml.update(readonly=True)

    loop = True
    data = {fname: old_fn, ext: old_ext, pattern: tmp_pl[0], replace: tmp_rl[0], root: old_root,
            key_new_root: '', key_new_base: ''}

    while loop:
        dst_from_data = os.path.join(data[key_new_root], data[key_new_base])
        try:
            tmp_fname = re_sub() or data[fname] + data[ext]
            dst = os.path.realpath(os.path.join(data[root], tmp_fname))
        except TypeError:
            dst = src
        if dst != dst_from_data:
            nr, nb = os.path.split(dst)
            window[key_new_root].update(nr)
            window[key_new_base].update(nb)
            window[bytes_count].update(count_name_bytes(nb))

        event, data = window.read()
        for k in (root, fname, ext, key_new_root, key_new_base):
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
                        shutil.move(info_filepath, os.path.splitext(dst)[0] + '.info')
                loop = False
            except FileNotFoundError:
                for k in (root, fname, ext):
                    window[k].update(text_color='red')
            except FileExistsError:
                for k in (key_new_root, key_new_base):
                    window[k].update(text_color='red')
            except OSError as e:
                G.PopupError(str(e))
        elif event in (None, cancel):
            loop = False
        else:
            ...
    else:
        write_json_file(conf_file, conf, indent=0)

    window.close()
