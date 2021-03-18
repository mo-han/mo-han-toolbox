#!/usr/bin/env python3
# encoding=utf8
import warnings

import keyboard
import mouse

from mylib.ez import *
from mylib.fstk import x_rename
from mylib.gui_old import rename_dialog
from mylib.ostk import clipboard
from mylib.uia import module_pywinauto

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
        const_complete_name = 'Complete name'

        t0 = time.time()
        clipboard.clear()
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
            if time.time() - t0 > timeout:
                raise TimeoutError
            self.gasp()
            try:
                text = clipboard.get() or ''
                lines = text.splitlines()
                line0 = getitem_default(lines, 0)
                line1 = getitem_default(lines, 1)
                if line0 == const_general and (line1.startswith(const_complete_name) or line1.startswith('Unique ID')):
                    break
            except clipboard.OpenError:
                warnings.warn('clipboard open error')

        space_and_colon = ' : '
        space_and_slash = ' / '
        data = current_node = {}
        for line in lines:
            if not line:
                continue
            if space_and_colon in line:
                k, v = line.split(space_and_colon, maxsplit=1)
                k: str = k.strip().lower()
                if space_and_slash in v:
                    v = v.split(space_and_slash)
            else:
                k, v = 'stream', line.strip().lower()
                type_name = v.split(' #')[0]
                if type_name == 'general':
                    current_node = data
                else:
                    current_node = {}
                    data.setdefault(type_name, []).append(current_node)
            current_node[k] = v

        try:
            data['path'] = data['complete name']
            video_stream_0: dict = data['video'][0]
            data['vc'] = video_stream_0['format'].lower()
            data['vbd'] = int(str_remove_suffix(video_stream_0['bit depth'], ' bits'))
            str_frame_rate = 'frame rate'
            str_original_frame_rate = 'original frame rate'
            if str_frame_rate in video_stream_0:
                data['fps'] = float(video_stream_0[str_frame_rate].split()[0])
            elif str_original_frame_rate in video_stream_0:
                data['fps'] = float(video_stream_0[str_original_frame_rate].split()[0])
            data['pix_fmt'] = video_stream_0['color space'].lower() + \
                              video_stream_0['chroma subsampling'].replace(':', '') + \
                              video_stream_0.get('scan type', 'p')
            data['h'] = int(str_remove_suffix(video_stream_0['height'], ' pixels').replace(' ', ''))
            data['w'] = int(str_remove_suffix(video_stream_0['width'], ' pixels').replace(' ', ''))
        except KeyError as e:
            print(repr(e))

        self._cache['fileinfo'] = data
        return data

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
