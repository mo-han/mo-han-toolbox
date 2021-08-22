#!/usr/bin/env python3
"""telegram bot utilities"""
import shlex
import traceback
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from inspect import getmembers, ismethod
from typing import Callable

from si_prefix import si_format
from telegram import ChatAction, Bot, Update, ParseMode, constants, Message, Chat
from telegram.ext import Updater, Filters, CallbackContext, PicklePersistence
from telegram.ext.filters import MergedFilter

from mylib.easy import ostk, text
from mylib.ex import fstk, tricks
from .easy import *
from .easy import python_module_from_source_code


def modify_telegram_ext_commandhandler(s: str) -> str:
    return s.replace('args = message.text.split()[1:]', 'args = self._get_args(message)')


telegram_ext_commandhandler_modified = python_module_from_source_code('telegram.ext.commandhandler',
                                                                      modify_telegram_ext_commandhandler)


class CommandHandler(telegram_ext_commandhandler_modified.CommandHandler):
    @staticmethod
    def _get_args(message: Message):
        return shlex.split(message.text)[1:]


class BotHandlerMethod(Callable):
    on_menu: bool
    handler: tuple


def deco_factory_bot_handler_method(handler_type, on_menu=False, **handler_kwargs):
    def deco(method: BotHandlerMethod) -> BotHandlerMethod:
        bot_handler_method = method
        bot_handler_method.on_menu = on_menu
        bot_handler_method.handler = handler_type, handler_kwargs
        return bot_handler_method

    return deco


def merge_filters_and(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, and_filter=y), filters)


def merge_filters_or(*filters):
    filters = list(set(filters) - {None})
    return reduce(lambda x, y: MergedFilter(x, or_filter=y), filters)


class SimpleBotTask:
    data: dict
    done = False


class SimpleBot(ABC):
    __task_queue__: queue.Queue
    __task_poll__: ThreadPoolExecutor
    __string_updates_unhandled__ = 'updates unhandled'
    __string_updates_unfinished__ = 'updates unfinished'

    def __init__(self, token, *,
                 timeout=None, whitelist=None, filters=None,
                 persistence_pickle_filename='telegram_bot.dat',
                 auto_run=True, debug_mode=False,
                 **kwargs):
        self.__timeout__ = timeout
        self.__filters__ = filters
        self._debug_mode = debug_mode

        self.__persistence__ = PicklePersistence(persistence_pickle_filename)
        self.__persistence__.get_bot_data()
        bot_data = self.__persistence__.bot_data
        self.__unhandled_updates__ = bot_data.setdefault(self.__string_updates_unhandled__, set())
        self.__unfinished_updates__ = bot_data.setdefault(self.__string_updates_unfinished__, set())
        self.__updater__ = Updater(token, use_context=True, persistence=self.__persistence__,
                                   request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                                   **kwargs)
        self.__restore_updates_into_queue()

        self.__get_me__()
        print(self.__about_this_bot__())
        self.__register_whitelist__(whitelist)
        self.__register_handlers__()
        if auto_run:
            self.__run__(poll_timeout=timeout)

    @property
    def __bot__(self) -> Bot:
        return self.__updater__.bot

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
                v: BotHandlerMethod
                _type, _kwargs = v.handler
                _kwargs: dict
                _kwargs['callback'] = v  # important
                if _type == CommandHandler:
                    command = _kwargs.setdefault('command', n)
                    self.__commands_list__.append((command, v))
                if self.__filters__:
                    _filters = _kwargs.get('filters')
                    _kwargs['filters'] = merge_filters_and(self.__filters__, _filters)
                self.__updater__.dispatcher.add_handler(_type(**_kwargs))

    def __get_me__(self):
        me = self.__bot__.get_me(timeout=self.__timeout__)
        fullname = me.first_name or ''
        last_name = me.last_name
        if last_name:
            fullname += f' {last_name}'
        self.__fullname__ = fullname
        self.__username__ = me.username
        return me

    def __typing__(self, update: Update):
        self.__bot__.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    def __send_text__(self, any_text: str, dst, **kwargs):
        if isinstance(dst, Update):
            def _send(sth):
                dst.message.reply_text(sth, **kwargs)
        elif isinstance(dst, (int, str)):
            def _send(sth):
                self.__bot__.send_message(dst, sth, **kwargs)
        else:
            raise TypeError(dst, (Update, int, str))
        if len(any_text) > constants.MAX_MESSAGE_LENGTH:
            for s in text.split_by_new_line_with_max_length(any_text, constants.MAX_MESSAGE_LENGTH):
                _send(s)
        else:
            _send(any_text)

    def __send_markdown__(self, md_text: str, dst, **kwargs):
        self.__send_text__(md_text, dst, parse_mode=ParseMode.MARKDOWN, **kwargs)

    __send_md__ = __send_markdown__

    def __send_code_block__(self, code_text, dst):
        for ct in text.split_by_new_line_with_max_length(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__send_markdown__(f'```\n{ct}```', dst)

    def __send_traceback__(self, dst):
        if not self._debug_mode:
            return
        tb = traceback.format_exc()
        print(tb)
        self.__send_code_block__(f'{tb}', dst)

    def __task_loop__(self):
        ...

    def __run__(self, poll_timeout=None):
        poll_param = {}
        if poll_timeout is not None:
            poll_param['timeout'] = poll_timeout
        self.__updater__.start_polling(**poll_param)
        self.__updater__.idle()

    def __get_menu_str__(self):
        lines = [f'try these commands:']
        menu = [n for n, v in self.__commands_list__ if v.on_menu]
        lines.extend([f'/{e}' for e in menu])
        return '\n'.join(lines)

    def __about_this_bot__(self):
        return f'''
bot:
{self.__fullname__} @{self.__username__}

on device:
{ostk.USERNAME} @ {ostk.HOSTNAME} ({ostk.OSNAME})

load {len(self.__unhandled_updates__)} unhandled and {len(self.__unfinished_updates__)} unfinished updates
'''.strip()

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True)
    def start(self, update: Update, context: CallbackContext):
        """let's roll out"""
        self.__typing__(update)
        self.__get_me__()
        update.message.reply_text(self.__about_this_bot__())
        update.message.reply_text(self.__get_menu_str__())

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True)
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
        self.__send_markdown__(f'```\n{menu_str}```', update)

    def __requeue_update__(self, update: Update):
        update_queue = self.__updater__.dispatcher.update_queue
        update_queue.put(update)
        s = f'''
{self.__requeue_update__.__name__}:
qsize={update_queue.qsize()}
'''.strip()
        print(s)
        self.__send_code_block__(s, update)

    def __snap_queued_updates__(self):
        self.__unhandled_updates__.update(self.__updater__.dispatcher.update_queue.queue)

    def __restore_updates_into_queue(self):
        q = self.__updater__.dispatcher.update_queue
        [q.put(u) for u in itertools.chain(self.__unhandled_updates__, self.__unfinished_updates__)]

    def __flush_persistence__(self, *, unfinished_updates: T.Iterable[Update] = ()):
        timer = Timer()
        self.__snap_queued_updates__()

        if isinstance(unfinished_updates, Update):
            unfinished_updates = [unfinished_updates]
        self.__unfinished_updates__.update(unfinished_updates)

        self.__persistence__.flush()
        timer.stop()
        print(
            f'save {len(self.__unhandled_updates__)} unhandled and {len(self.__unfinished_updates__)} unfinished '
            f'updates in {timer.duration:.1f}s')
