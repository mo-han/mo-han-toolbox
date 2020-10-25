#!/usr/bin/env python3
# encoding=utf8
"""telegram bot utilities"""
from functools import reduce
from inspect import getmembers, ismethod
from queue import Queue
from typing import Callable

from telegram import ChatAction, Bot, Update, ParseMode, constants
from telegram.ext import Updater, CommandHandler, Filters, CallbackContext
from telegram.ext.filters import MergedFilter

from .os_util import get_names
from .text import split_by_length_and_lf
from .tricks import Decorator


def meta_deco_handler_method(handler_type, is_specialty=False, **handler_kwargs) -> Decorator:
    def deco(handler_method: Callable):
        wrap = handler_method
        wrap.is_specialty = is_specialty
        wrap.handler_registry = handler_type, handler_kwargs
        return wrap

    return deco


def merge_filters_and(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, and_filter=y), filters)


def merge_filters_or(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, or_filter=y), filters)


class SimpleBot:
    def __init__(self, token, *, timeout=None, whitelist=None, auto_run=True,
                 filters=None, update_queue: Queue = None,
                 **kwargs):
        self.failed_updates = []
        self.device = get_names()
        self.updater = Updater(token, use_context=True,
                               request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                               **kwargs)
        self.bot: Bot = self.updater.bot
        self.__get_me__(timeout=timeout)
        self.common_filters = filters
        if whitelist:
            chat_id_filter = Filters.chat(filter(lambda x: isinstance(x, int), whitelist))
            chat_username_filter = Filters.chat(filter(lambda x: isinstance(x, str), whitelist))
            self.common_filters = merge_filters_and(self.common_filters, chat_id_filter | chat_username_filter)
            for u in whitelist:
                if isinstance(u, int):
                    self.bot.send_message(u, self.__about_this_bot__())
        self.__register_handlers__()
        if auto_run:
            self.__run__(poll_timeout=timeout)

    def __register_handlers__(self):
        self.commands_list = []
        for n, v in getmembers(self):
            if ismethod(v) and hasattr(v, 'handler_registry'):
                _type, _kwargs = v.handler_registry
                _kwargs['callback'] = v
                if _type == CommandHandler:
                    self.commands_list.append((n, v))
                    if 'command' not in _kwargs:
                        _kwargs['command'] = n
                if self.common_filters:
                    _filters = _kwargs.get('filters')
                    _kwargs['filters'] = merge_filters_and(self.common_filters, _filters)
                self.updater.dispatcher.add_handler(_type(**_kwargs))

    def __get_me__(self, timeout=None):
        self.me = self.bot.get_me(timeout=timeout)
        fullname = self.me.first_name or ''
        last_name = self.me.last_name
        if last_name:
            fullname += f' {last_name}'
        self.fullname = fullname
        self.username = self.me.username

    def __typing__(self, update: Update):
        self.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    @staticmethod
    def __reply_text__(text, update: Update, **kwargs):
        for t in split_by_length_and_lf(text, constants.MAX_MESSAGE_LENGTH):
            update.message.reply_text(t, **kwargs)

    def __reply_markdown__(self, md_text, update: Update):
        self.__reply_text__(md_text, update, parse_mode=ParseMode.MARKDOWN)

    __reply_md__ = __reply_markdown__

    def __reply_md_code_block__(self, code_text, update: Update):
        for ct in split_by_length_and_lf(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__reply_markdown__(f'```\n{ct}```', update)

    def __run__(self, poll_timeout=None):
        poll_param = {}
        if poll_timeout is not None:
            poll_param['timeout'] = poll_timeout
        self.updater.start_polling(**poll_param)
        self.updater.idle()

    def __specialty_menu__(self):
        lines = [f'try these commands:']
        specialty_menu = [n for n, v in self.commands_list if v.is_specialty]
        lines.extend([f'/{e}' for e in specialty_menu])
        return '\n'.join(lines)

    def __about_this_bot__(self):
        return f'bot:\n' \
               f'{self.fullname} @{self.username}\n\n' \
               f'running on device:\n' \
               f'{self.device.username} @ {self.device.hostname} ({self.device.osname})'

    @meta_deco_handler_method(CommandHandler, is_specialty=True)
    def start(self, update: Update, context: CallbackContext):
        """let's roll out"""
        self.__typing__(update)
        self.__get_me__()
        update.message.reply_text(self.__about_this_bot__())
        update.message.reply_text(self.__specialty_menu__())

    @meta_deco_handler_method(CommandHandler, is_specialty=True)
    def menu(self, update: Update, context: CallbackContext):
        """list commands"""
        self.__typing__(update)
        lines = []
        for n, v in self.commands_list:
            if n.startswith('_'):
                continue
            doc = (v.__doc__ or '...').split('\n', maxsplit=1)[0].strip()
            lines.append(f'{n} - {doc}')
        menu_str = '\n'.join(lines)
        self.__reply_markdown__(f'```\n{menu_str}```', update)
