#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

from time import sleep, time, strftime
import logging

from pyautogui import \
    locateOnScreen, locateCenterOnScreen, \
    moveTo, moveRel, click, hotkey
from pywinauto import \
    handleprops, win32functions, keyboard

__author__ = '墨焓 <zmhungrown@gmail.com>'
__program__ = 'dota2 lib'
__version__ = 'demo'

_logger = logging.getLogger(__program__)

button_of_accept = 'button_of_accept.png'
box_of_game_ready = 'box_of_game_ready.png'

fg_window = win32functions.GetForegroundWindow
fgw_title = lambda: handleprops.text(fg_window())
fgw_class = lambda: handleprops.classname(fg_window())


def dota2_accept_game_and_switch_back():
    hotkey('enter')
    hotkey('alt', 'tab')


class Dota2Controller:

    TIME_SLOT = 0.1
    POLL_INTERVAL_MAX = 10
    WINDOW_INFO = {'title': 'Dota 2', 'class': 'SDL_app', 'program': 'dota2.exe'}
#    WINDOW_INFO = {'class': 'HoneyviewClassX'}

    poll_interval = TIME_SLOT
    last_fg = float()
    last_bg = float()
    material = {
        'accept': button_of_accept,
        'game_ready': box_of_game_ready,
    }

    def __init__(self, material_dir: str= ''):
        self.last_fg = time()
        self.last_bg = time()
        self.path_prefix = material_dir
        for k,v in self.material.items():
            self.material[k] = '/'.join((self.path_prefix, v))

    @staticmethod
    def datetime():
        return strftime('%Y-%m-%d %H:%M:%S')

    def is_fg(self):
        """`fg`=foreground, `bg`=background
        """
        # Polling interval...
        if self.poll_interval > self.POLL_INTERVAL_MAX:
            sleep(self.POLL_INTERVAL_MAX)
        else:
            sleep(self.poll_interval)
        # Check if in foreground or not, changing polling interval dynamically.
#        if fgw_title() != self.WINDOW_INFO['title'] or fgw_class() != self.WINDOW_INFO['class']:
        if fgw_class() != self.WINDOW_INFO['class']:
            self.last_bg = time()
            if time() - self.last_fg >= 300:
                self.poll_interval = 10 * self.TIME_SLOT
            elif time() - self.last_fg >= 60:
                self.poll_interval = 2 * self.TIME_SLOT
            else:
                self.poll_interval = self.TIME_SLOT
            return False
        else:
            self.last_fg = time()
            if time() - self.last_bg >= 300:
                self.poll_interval = 50 * self.TIME_SLOT
            elif time() - self.last_bg >= 60:
                self.poll_interval = 10 * self.TIME_SLOT
            else:
                self.poll_interval = self.TIME_SLOT
            return True

    def accept_then_back(self):
        if locateOnScreen(self.material['game_ready'], grayscale=True) or locateOnScreen(self.material['accept'], grayscale=True):
            print('NEW GAME', end='\r')
            keyboard.send_keys('{ENTER}')
            sleep(self.TIME_SLOT)
            keyboard.send_keys('{ENTER}')
            sleep(self.TIME_SLOT)
            hotkey('alt', 'tab')

    def auto_waiter(self, show_trend=(0, 0)):
        last = time()
        history = [self.poll_interval]
        while True:
            if self.is_fg():
                print('DOTA2', end='\r')
                sleep(0.1)
                self.accept_then_back()
            if show_trend[0]:
                now = time()
                if now - last >= show_trend[0]:
                    if self.poll_interval != history[-1]:
                        history.append(self.poll_interval)
                        history = history[-show_trend[1]:]
                    last = now