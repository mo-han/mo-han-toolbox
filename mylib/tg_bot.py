#!/usr/bin/env python3
# encoding=utf8
"""telegram bot utilities"""
from functools import reduce
from inspect import getmembers, ismethod
from pprint import pformat
from typing import Callable

from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, Filters, Defaults
from telegram.ext.filters import MergedFilter

from .os_util import get_names
from .tricks import Decorator


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
        self.bot = self.updater.bot
        self.__update_me__(timeout=timeout)
        self.common_filters = filters
        if user_whitelist:
            chat_id_filter = Filters.chat(filter(lambda x: isinstance(x, int), user_whitelist))
            chat_username_filter = Filters.chat(filter(lambda x: isinstance(x, str), user_whitelist))
            self.common_filters = merge_filters_and(self.common_filters, chat_id_filter | chat_username_filter)
        self.pre_handler = []
        self.post_handler = []
        self.__register_handlers__()
        if auto_run:
            self.__bot_run__(poll_timeout=timeout)

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

    def __update_me__(self, timeout=None):
        self.me = self.bot.get_me(timeout=timeout)
        fullname = self.me.first_name or ''
        last_name = self.me.last_name
        if last_name:
            fullname += f' {last_name}'
        self.fullname = fullname
        self.username = self.me.username

    def __send_action_typing__(self, update):
        self.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    def __bot_run__(self, poll_timeout=None):
        poll_param = {}
        if poll_timeout is not None:
            poll_param['timeout'] = poll_timeout
        self.updater.start_polling(**poll_param)
        self.updater.idle()

    def __suggest_commands(self):
        lines = [f'try these commands:']
        methods = [self.start, self.test, self.menu]
        lines.extend([f'/{e.__name__}' for e in methods])
        return '\n'.join(lines)

    @meta_deco_handler_method(CommandHandler)
    def start(self, update, context):
        self.__send_action_typing__(update)
        self.__update_me__()
        update.message.reply_text(
            f'bot running:\n{self.fullname} @{self.username}\n'
            f'on device:\n{self.device.username} @ {self.device.hostname} ({self.device.osname})')
        update.message.reply_text(self.__suggest_commands())

    @meta_deco_handler_method(CommandHandler)
    def test(self, update, context):
        self.__send_action_typing__(update)
        for name in ('effective_message', 'effective_user'):
            update.message.reply_text(name)
            update.message.reply_text(pformat(getattr(update, name).to_dict()))
        update.message.reply_text('bot.get_me()')
        update.message.reply_text(pformat(self.bot.get_me().to_dict()))

    @meta_deco_handler_method(CommandHandler)
    def menu(self, update, context):
        """list all commands"""
        lines = []
        for n, v in self.commands_list:
            doc = (v.__doc__ or '...').split('\n', maxsplit=1)[0].strip()
            lines.append(f'{n} - {doc}')
        update.message.reply_text('\n'.join(lines))
