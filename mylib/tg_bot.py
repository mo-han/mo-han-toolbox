#!/usr/bin/env python3
# encoding=utf8
"""telegram bot utilities"""
from functools import reduce
from inspect import getmembers, ismethod
from typing import Callable

from telegram import ChatAction, Bot, Update, ParseMode, constants
from telegram.ext import Updater, CommandHandler, Filters
from telegram.ext.filters import MergedFilter

from .os_util import get_names
from .tricks import Decorator
from .text import split_by_length_and_lf


def meta_deco_handler_method(handler_type, **handler_kwargs) -> Decorator:
    def deco(handler_method: Callable):
        wrap = handler_method
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
    def __init__(self, token, auto_run=True, user_whitelist=None, timeout=None,
                 filters=None, **kwargs):
        self.device = get_names()
        self.updater = Updater(token, use_context=True,
                               request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                               **kwargs)
        self.bot: Bot = self.updater.bot
        self.__get_me__(timeout=timeout)
        self.common_filters = filters
        if user_whitelist:
            chat_id_filter = Filters.chat(filter(lambda x: isinstance(x, int), user_whitelist))
            chat_username_filter = Filters.chat(filter(lambda x: isinstance(x, str), user_whitelist))
            self.common_filters = merge_filters_and(self.common_filters, chat_id_filter | chat_username_filter)
            for u in user_whitelist:
                if isinstance(u, int):
                    self.bot.send_message(u, self.__about_this_bot__())
        self.pre_handler = []
        self.post_handler = []
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
    def __reply_text__(update: Update, text, **kwargs):
        for t in split_by_length_and_lf(text, constants.MAX_MESSAGE_LENGTH):
            update.message.reply_text(t, **kwargs)

    def __reply_markdown__(self, update: Update, md_text):
        self.__reply_text__(update, md_text, parse_mode=ParseMode.MARKDOWN)

    __reply_md__ = __reply_markdown__

    def __reply_md_code_block__(self, update: Update, code_text):
        for ct in split_by_length_and_lf(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__reply_markdown__(update, f'```\n{ct}```')

    def __run__(self, poll_timeout=None):
        poll_param = {}
        if poll_timeout is not None:
            poll_param['timeout'] = poll_timeout
        self.updater.start_polling(**poll_param)
        self.updater.idle()

    def __recommended_commands__(self):
        lines = [f'try these commands:']
        recommended = [n for n, v in self.commands_list if
                       hasattr(v, 'handler_xattr') and 'recommended' in v.handler_xattr]
        lines.extend([f'/{e}' for e in recommended])
        return '\n'.join(lines)

    def __about_this_bot__(self):
        return f'bot:\n' \
               f'{self.fullname} @{self.username}\n\n' \
               f'running on device:\n' \
               f'{self.device.username} @ {self.device.hostname} ({self.device.osname})'

    @meta_deco_handler_method(CommandHandler)
    def start(self, update: Update, context):
        """let's roll out"""
        self.__typing__(update)
        self.__get_me__()
        update.message.reply_text(self.__about_this_bot__())
        update.message.reply_text(self.__recommended_commands__())

    start.handler_xattr = ['recommended']

    @meta_deco_handler_method(CommandHandler)
    def menu(self, update: Update, context):
        """list commands"""
        self.__typing__(update)
        lines = []
        for n, v in self.commands_list:
            if n.startswith('_'):
                continue
            doc = (v.__doc__ or '...').split('\n', maxsplit=1)[0].strip()
            lines.append(f'{n} - {doc}')
        menu_str = '\n'.join(lines)
        self.__reply_markdown__(update, f'```\n{menu_str}```')

    menu.handler_xattr = ['recommended']
