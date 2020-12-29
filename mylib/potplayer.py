#!/usr/bin/env python3
# encoding=utf8
import warnings
from time import sleep, time

import keyboard
import mouse

from .gui import rename_dialog
from .uia import module_pywinauto
from .os_auto import clipboard
from .fs import x_rename

pywinauto = module_pywinauto()
App = pywinauto.Application
HwndElementInfo = pywinauto.win32_element_info.HwndElementInfo
find_elements = pywinauto.findwindows.find_elements


class PotPlayerKit:
    def __init__(self, gasp_time: int or float = 0.01):
        # import warnings
        # warnings.simplefilter('ignore', category=UserWarning)
        self.gasp_time = gasp_time
        self._window = App().connect(handle=self.list[0].handle).window()
        self._cache = {'fileinfo': {}}

    def select(self, element: HwndElementInfo):
        self._window = App().connect(handle=element.handle)

    def gasp(self, t: int or float = None):
        t = t or self.gasp_time
        sleep(t)

    @property
    def cache(self):
        return self._cache

    @property
    def current(self):
        return self._window

    @property
    def list(self):
        return find_elements(class_name_re='PotPlayer(64)?')

    def focus(self):
        old_coord = mouse.get_position()
        while True:
            try:
                self.current.set_focus()
                break
            except pywinauto.findwindows.ElementAmbiguousError:
                print('! ambiguous potplayer window , check it')
                self.gasp(1)
        mouse.move(*old_coord)
        self.gasp()

    @property
    def fileinfo(self):
        return self.cache['fileinfo']

    def get_fileinfo(self, alt_tab: bool = True, timeout=5):
        const_general = 'General'
        const_general_lower = const_general.lower()
        const_complete_name = 'Complete name'
        const_complete_name_lower = const_complete_name.lower()

        t0 = time()
        clipboard.del_bot()
        self.focus()
        keyboard.press_and_release('ctrl+f1')
        for _ in range(5):
            keyboard.press_and_release('shift+tab')
        keyboard.press_and_release('enter')
        self.gasp()
        keyboard.press_and_release('alt+p, esc')
        self.gasp()
        if alt_tab:
            keyboard.press_and_release('alt+tab')

        while True:
            if time() - t0 > timeout:
                raise TimeoutError
            self.gasp()
            try:
                data = clipboard.get() or ''
                lines = data.splitlines()
                line0 = getitem_default(lines, 0)
                line1 = getitem_default(lines, 1)
                if line0 == const_general and (line1.startswith(const_complete_name) or line1.startswith('Unique ID')):
                    break
            except clipboard.OpenError:
                warnings.warn('clipboard open error')

        d = {}
        group = ''
        stream_id = -1
        for line in lines:
            if ':' in line:
                k, v = [e.strip() for e in line.split(':', maxsplit=1)]
                k = k.lower()
                if k == 'id':
                    d[group].append({})
                    stream_id += 1
                    continue
                elif k == 'encoding settings':
                    v = [e.strip() for e in v.split('/')]
                if group == const_general_lower:
                    if k == 'attachments':
                        d[k] = v.split(' / ')
                    else:
                        d[k] = v
                elif group:
                    d[group][stream_id][k] = v
            else:
                g = line.strip().lower().split(' #', maxsplit=1)[0]
                if g and g != group:
                    if g != const_general_lower:
                        d[g] = []
                    group = g
                    stream_id = -1

        try:
            d['path'] = d[const_complete_name_lower]
            vs0 = d['video'][0]
            d['vc'] = vs0['format'].lower()
            d['vbd'] = int(vs0['bit depth'].rstrip(' bits'))
            if 'frame rate' in vs0:
                d['fps'] = float(vs0['frame rate'].split()[0])
            elif 'original frame rate' in vs0:
                d['fps'] = float(vs0['original frame rate'].split()[0])
            d['pix_fmt'] = \
                vs0['color space'].lower() + \
                vs0['chroma subsampling'].replace(':', '') + \
                vs0['scan type'][0].lower() if 'scan type' in vs0 else 'p'
            d['h'] = int(vs0['height'].rstrip(' pixels').replace(' ', ''))
            d['w'] = int(vs0['width'].rstrip(' pixels').replace(' ', ''))
        except KeyError as e:
            print(repr(e))

        self._cache['fileinfo'] = d
        return d

    def rename_file(self, new: str, use_cache: bool = False, move_to: str = None, keep_ext: bool = True):
        fileinfo = self.cache['fileinfo'] if use_cache else self.get_fileinfo()
        src = fileinfo['path']
        x_rename(src, new, move_to_dir=move_to, append_src_ext=keep_ext)

    def rename_file_gui(self, alt_tab: bool = False):
        try:
            fileinfo = self.get_fileinfo(alt_tab=alt_tab)
        except TimeoutError:
            print('! TIMEOUT: clipboard data')
            return
        src = fileinfo['path']
        rename_dialog(src)


def getitem_default(x, index_or_key, default=None):
    try:
        return x[index_or_key]
    except (IndexError, KeyError):
        return default