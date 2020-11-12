#!/usr/bin/env python3
# encoding=utf8
"""telegram bot utilities"""
import time
from abc import ABC
from functools import reduce
from inspect import getmembers, ismethod
from queue import Queue
from typing import Callable

from telegram import ChatAction, Bot, Update, ParseMode, constants
from telegram.ext import Updater, CommandHandler, Filters, CallbackContext
from telegram.ext.filters import MergedFilter

from .os_util import get_names
from .text import split_by_length_or_lf
from .tricks import Decorator


def meta_deco_handler_method(handler_type, on_menu=False, **handler_kwargs) -> Decorator:
    def deco(handler_method: Callable):
        wrap = handler_method
        wrap.on_menu = on_menu
        wrap.handler = handler_type, handler_kwargs
        return wrap

    return deco


def merge_filters_and(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, and_filter=y), filters)


def merge_filters_or(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, or_filter=y), filters)


class SimpleBot(ABC):
    def __init__(self, token, *, timeout=None, whitelist=None, auto_run=True, data: dict = None, filters=None,
                 **kwargs):
        self.__data__ = data or {}
        self.__filters__ = filters
        self.__device__ = get_names()
        self.__updater__ = Updater(token, use_context=True,
                                   request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                                   **kwargs)
        self.__bot__: Bot = self.__updater__.bot
        self.__get_me__(timeout=timeout)
        self.__data_init__()
        print(self.__about_this_bot__())
        self.__register_whitelist__(whitelist)
        self.__register_handlers__()
        if auto_run:
            self.__run__(poll_timeout=timeout)

    def __register_whitelist__(self, whitelist):
        if whitelist:
            chat_id_filter = Filters.chat(list(filter(lambda x: isinstance(x, int), whitelist)))
            chat_username_filter = Filters.chat(list(filter(lambda x: isinstance(x, str), whitelist)))
            self.__filters__ = merge_filters_and(self.__filters__, chat_id_filter | chat_username_filter)
            for u in whitelist:
                if isinstance(u, int):
                    self.__bot__.send_message(u, self.__about_this_bot__())

    def __register_handlers__(self):
        self.__commands_list__ = []
        for n, v in getmembers(self):
            if ismethod(v) and hasattr(v, 'handler'):
                _type, _kwargs = v.handler
                _kwargs['callback'] = v
                if _type == CommandHandler:
                    self.__commands_list__.append((n, v))
                    if 'command' not in _kwargs:
                        _kwargs['command'] = n
                if self.__filters__:
                    _filters = _kwargs.get('filters')
                    _kwargs['filters'] = merge_filters_and(self.__filters__, _filters)
                self.__updater__.dispatcher.add_handler(_type(**_kwargs))

    def __get_me__(self, timeout=None):
        me = self.__bot__.get_me(timeout=timeout)
        fullname = me.first_name or ''
        last_name = me.last_name
        if last_name:
            fullname += f' {last_name}'
        self.__fullname__ = fullname
        self.__username__ = me.username
        return me

    def __typing__(self, update: Update):
        self.__bot__.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    @staticmethod
    def __reply_text__(text, update: Update, **kwargs):
        for t in split_by_length_or_lf(text, constants.MAX_MESSAGE_LENGTH):
            update.message.reply_text(t, **kwargs)

    def __reply_markdown__(self, md_text, update: Update):
        self.__reply_text__(md_text, update, parse_mode=ParseMode.MARKDOWN)

    __reply_md__ = __reply_markdown__

    def __reply_md_code_block__(self, code_text, update: Update):
        for ct in split_by_length_or_lf(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__reply_markdown__(f'```\n{ct}```', update)

    def __run__(self, poll_timeout=None):
        poll_param = {}
        if poll_timeout is not None:
            poll_param['timeout'] = poll_timeout
        self.__updater__.start_polling(**poll_param)
        self.__updater__.idle()

    def __menu_str__(self):
        lines = [f'try these commands:']
        menu = [n for n, v in self.__commands_list__ if v.on_menu]
        lines.extend([f'/{e}' for e in menu])
        return '\n'.join(lines)

    def __about_this_bot__(self):
        return f'bot:\n' \
               f'{self.__fullname__} @{self.__username__}\n\n' \
               f'running on device:\n' \
               f'{self.__device__.username} @ {self.__device__.hostname} ({self.__device__.osname})\n\n' \
               f'resume {self.__data__["update_queue.qsize"]} update(s) from {self.__data__["mtime"]}'

    @meta_deco_handler_method(CommandHandler, on_menu=True)
    def start(self, update: Update, context: CallbackContext):
        """let's roll out"""
        self.__typing__(update)
        self.__get_me__()
        update.message.reply_text(self.__about_this_bot__())
        update.message.reply_text(self.__menu_str__())

    @meta_deco_handler_method(CommandHandler, on_menu=True)
    def menu(self, update: Update, context: CallbackContext):
        """list commands"""
        self.__typing__(update)
        lines = []
        for n, v in self.__commands_list__:
            if n.startswith('_'):
                continue
            doc = (v.__doc__ or '...').split('\n', maxsplit=1)[0].strip()
            lines.append(f'{n} - {doc}')
        menu_str = '\n'.join(lines)
        self.__reply_markdown__(f'```\n{menu_str}```', update)

    def __data_save__(self):
        self.__data__['mtime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def __requeue_failed_update__(self, update: Update, save=False):
        # failed_updates = self.__data__['failed_updates']
        # if update not in failed_updates:
        #     failed_updates.append(update)
        update_queue = self.__updater__.dispatcher.update_queue
        update_queue.put(update)
        qsize = update_queue.qsize()
        self.__data__['update_queue.qsize'] = qsize
        s = f'{self.__requeue_failed_update__.__name__}: qsize={qsize}'
        print(s)
        self.__reply_md_code_block__(s, update)
        if save:
            self.__data_save__()

    def __data_init__(self):
        # [self.__updater__.dispatcher.update_queue.put(u) for u in self.__data__.setdefault('failed_updates', [])]
        self.__data__.setdefault('mtime', 'N/A')
        update_queue = self.__data__.setdefault('update_queue', Queue())
        self.__data__['update_queue.qsize'] = update_queue.qsize()
        while update_queue.qsize():
            update = update_queue.get()
            self.__updater__.dispatcher.update_queue.put(update)
