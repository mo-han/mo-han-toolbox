#!/usr/bin/env python3
# encoding=utf8
"""telegram bot utilities"""
import itertools
import shlex
import traceback
from abc import ABC
from functools import reduce
from inspect import getmembers, ismethod
from typing import Callable

from si_prefix import si_format
from telegram import ChatAction, Bot, Update, ParseMode, constants, Message
from telegram.ext import Updater, Filters, CallbackContext
from telegram.ext.filters import MergedFilter

from . import T
from .ez import *
from .fstk import write_sqlite_dict_file, read_sqlite_dict_file
from .os_auto import HOSTNAME, OSNAME, USERNAME
from .text import split_by_length_or_newline
from .tricks import modify_module, deep_setattr, walk_obj_iter, is_picklable_with_dill_trace


class BotPlaceholder:
    pass


BOT_PLACEHOLDER = BP = BotPlaceholder()


def modify_telegram_ext_commandhandler(s: str) -> str:
    return s.replace('args = message.text.split()[1:]', 'args = self._get_args(message)')


telegram_ext_commandhandler_modified = modify_module('telegram.ext.commandhandler', modify_telegram_ext_commandhandler)


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


class SimpleBot(ABC):
    def __init__(self, token, *,
                 timeout=None, whitelist=None, filters=None, runtime_data: dict = None,
                 auto_run=True, debug_mode=False,
                 **kwargs):
        self._debug_mode = debug_mode
        self.__rt_data__ = runtime_data or {}
        self.__filters__ = filters
        self.__updater__ = Updater(token, use_context=True,
                                   request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                                   **kwargs)
        self.__get_me__(timeout=timeout)
        self.__init_rt_data__()
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
            v: BotHandlerMethod
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
        for t in split_by_length_or_newline(text, constants.MAX_MESSAGE_LENGTH):
            update.message.reply_text(t, **kwargs)

    def __reply_markdown__(self, md_text, update: Update):
        self.__reply_text__(md_text, update, parse_mode=ParseMode.MARKDOWN)

    __reply_md__ = __reply_markdown__

    def __reply_md_code_block__(self, code_text, update: Update):
        for ct in split_by_length_or_newline(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__reply_markdown__(f'```\n{ct}```', update)

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
        return f'bot:\n' \
               f'{self.__fullname__} @{self.__username__}\n\n' \
               f'running on device:\n' \
               f'{USERNAME} @ {HOSTNAME} ({OSNAME})\n\n' \
               f'load {len(self.__rt_data__["queued"]) + len(self.__rt_data__["undone"])} update(s) ' \
               f'since {self.__rt_data__["mtime"]}'

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
        self.__reply_markdown__(f'```\n{menu_str}```', update)

    def __save_rt_data__(self, data_file_path=None):
        # def pickle_bot(bot_obj: Bot):
        #     return (lambda: self.__bot__), ()
        # copyreg.pickle(Bot, pickle_bot)
        # ABOVE CODE IS NOT A SOLUTION!
        t0 = time.perf_counter()
        data = self.__rt_data__
        data['mtime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if data_file_path:
            undone = data.setdefault('undone', {})
            queued = data.setdefault('queued', [])
            updates: T.List[Update] = [*undone.values(), *queued]
            [self.__pre_pickle_update__(u) for u in updates]
            write_sqlite_dict_file(data_file_path, data, with_dill=True)
            [self.__post_pickle_update__(u) for u in updates]
            read_data = read_sqlite_dict_file(data_file_path, with_dill=True)
            t = time.perf_counter() - t0
            print(f'saved: {len(read_data["undone"])} undone, {len(read_data["queued"])} queued ({si_format(t)}s used)')

    def __pre_pickle_update_auto__(self, u: Update):
        for p in (path for path, obj in walk_obj_iter(u, keepout_types=(Bot,)) if isinstance(obj, Bot)):
            deep_setattr(u, BP, *p)
        if self._debug_mode and not is_picklable_with_dill_trace(u):
            for p in (path for path, obj in walk_obj_iter(u, keepout_types=(Bot,)) if isinstance(obj, Bot)):
                print(p)

    def __post_pickle_update_auto__(self, u: Update):
        for p in (path for path, obj in walk_obj_iter(u, keepout_types=(BotPlaceholder,)) if
                  isinstance(obj, BotPlaceholder)):
            deep_setattr(u, self.__bot__, *p)

    def __pre_pickle_update__(self, u: Update):
        msg = u.message
        msg.bot = msg.from_user.bot = msg.chat.bot = BP
        if self._debug_mode and not is_picklable_with_dill_trace(u):
            for p in (path for path, obj in walk_obj_iter(u, keepout_types=(Bot,)) if isinstance(obj, Bot)):
                print(p)

    def __post_pickle_update__(self, u: Update):
        msg = u.message
        msg.bot = msg.from_user.bot = msg.chat.bot = self.__bot__

    def __requeue_failed_update__(self, update: Update, save=False):
        update_queue = self.__updater__.dispatcher.update_queue
        update_queue.put(update)
        s = f'{self.__requeue_failed_update__.__name__}: qsize={update_queue.qsize()}'
        print(s)
        self.__reply_md_code_block__(s, update)
        if save:
            self.__save_rt_data__()

    def __init_rt_data__(self):
        self.__rt_data__.setdefault('mtime', 'N/A')
        undone = self.__rt_data__.setdefault('undone', {})
        queued = self.__rt_data__.setdefault('queued', [])
        for update in itertools.chain(undone.values(), queued):
            update.message.bot = self.__bot__
        [self.__updater__.dispatcher.update_queue.put(u) for u in queued]
        [self.__updater__.dispatcher.update_queue.put(v) for k, v in undone.items()]

    def __add_undone_update__(self, key: str, update: Update):
        self.__rt_data__['undone'][key] = update
        try:
            self.__save_rt_data__()
        except:
            self.__reply_md_code_block__(f'{traceback.format_exc()}', update)

    def __del_undone_update__(self, key: str, update: Update):
        del self.__rt_data__['undone'][key]
        try:
            self.__save_rt_data__()
        except:
            self.__reply_md_code_block__(f'{traceback.format_exc()}', update)
