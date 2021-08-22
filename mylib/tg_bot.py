#!/usr/bin/env python3
"""telegram bot utilities"""
import shlex
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from inspect import getmembers, ismethod
from typing import Callable

import dill
import telegram.ext.picklepersistence
from telegram import ChatAction, Bot, Update, ParseMode, constants, Message
from telegram.ext import Updater, Filters, CallbackContext
from telegram.ext.filters import MergedFilter

from mylib.easy import ostk, text
from .easy import *
from .easy import python_module_from_source_code

telegram.ext.picklepersistence.pickle.dump = dill.dump
telegram.ext.picklepersistence.pickle.load = dill.load
PicklePersistence = telegram.ext.picklepersistence.PicklePersistence


class BotPlaceholder(metaclass=SingletonMetaClass):
    pass


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


class BotInternalCallResult(EzAttrData):
    ok: bool


class EasyBot:
    __task_queue__: queue.Queue
    __task_poll__: ThreadPoolExecutor
    __string_saved_updates__ = '__string_saved_updates__'
    __string_saved_calls__ = '__string_saved_calls__'

    def __init__(self, token, *,
                 timeout=None, whitelist=None, filters=None,
                 persistence_filename='telegram_bot.dat',
                 auto_run=True, debug_mode=False,
                 **kwargs):
        self.__timeout__ = timeout
        self.__filters__ = filters
        self._debug_mode = debug_mode

        self.__persistence_filename__ = persistence_filename
        self.__persistence_backup_filename__ = persistence_filename + '.bak'
        self.__persistence__ = self.__load_persistence__()
        bot_data: dict = self.__persistence__.bot_data
        self.__saved_updates__: set = bot_data.setdefault(self.__string_saved_updates__, set())
        self.__saved_calls__: T.Set[T.Tuple[tuple, dict]] = bot_data.setdefault(self.__string_saved_calls__, set())
        self.__updater__ = Updater(token, use_context=True, persistence=self.__persistence__,
                                   request_kwargs={'read_timeout': timeout, 'connect_timeout': timeout},
                                   **kwargs)
        self.__get_me__()
        print(self.__about_this_bot__())
        self.__restore_updates_into_queue__()
        self.__handle_saved_calls__()

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

    def __send_text__(self, dst, any_text: str, **kwargs):
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

    def __send_markdown__(self, dst, md_text: str, **kwargs):
        self.__send_text__(dst, md_text, parse_mode=ParseMode.MARKDOWN, **kwargs)

    __send_md__ = __send_markdown__

    def __send_code_block__(self, dst, code_text):
        for ct in text.split_by_new_line_with_max_length(code_text, constants.MAX_MESSAGE_LENGTH - 7):
            self.__send_markdown__(dst, f'```\n{ct}```')

    def __send_traceback__(self, dst):
        if not self._debug_mode:
            return
        tb = traceback.format_exc()
        print(tb)
        self.__send_code_block__(dst, f'{tb}')

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

load:
{len(self.__saved_calls__)} calls
{len(self.__saved_updates__)} updates
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
        self.__send_markdown__(update, f'```\n{menu_str}```')

    def __requeue_update__(self, update: Update):
        update_queue = self.__updater__.dispatcher.update_queue
        update_queue.put(update)
        s = f'''
{self.__requeue_update__.__name__}:
qsize={update_queue.qsize()}
'''.strip()
        print(s)
        self.__send_code_block__(update, s)

    def __restore_updates_into_queue__(self):
        q = self.__updater__.dispatcher.update_queue
        while self.__saved_updates__:
            u: Update = self.__saved_updates__.pop()
            # msg = u.message
            # msg.bot = msg.from_user.bot = msg.chat.bot = self.__bot__
            q.put(u)

    def __dump_persistence__(self):
        with Timer() as t:
            self.__saved_updates__ = set(self.__updater__.dispatcher.update_queue.queue)
            self.__persistence__.flush()
            if path_is_file(self.__persistence_filename__):
                shutil.copy(self.__persistence_filename__, self.__persistence_backup_filename__)
            print(f'''
save:
{len(self.__saved_calls__)} calls
{len(self.__saved_updates__)} updates
in {t.duration:.3f}s
'''.strip())

    def __load_persistence__(self):
        if path_is_file(self.__persistence_backup_filename__):
            shutil.copy(self.__persistence_backup_filename__, self.__persistence_filename__)
        persistence = PicklePersistence(self.__persistence_filename__)
        persistence.get_bot_data()
        persistence.get_chat_data()
        persistence.get_user_data()
        # persistence.get_conversations(...)
        persistence.get_callback_data()
        return persistence

    def __handle_saved_calls__(self):
        calls = self.__saved_calls__
        while calls:
            args, kwargs = dill.loads(calls.pop())
            if not self.__successful_internal_call__(*args, **kwargs):
                calls.add((args, kwargs))
            self.__dump_persistence__()

    @staticmethod
    def __new_internal_call_tuple__(*args, **kwargs) -> tuple:
        return args, kwargs

    def __add_internal_call__(self, target, *args, **kwargs):
        if not isinstance(target, str) and hasattr(target, '__name__'):
            target = target.__name__
        t = self.__new_internal_call_tuple__(target, *args, **kwargs)
        self.__saved_calls__.add(dill.dumps(t))
        self.__dump_persistence__()

    def __successful_internal_call__(self, *args, **kwargs) -> bool:
        target, *args = args
        if isinstance(target, str):
            target = getattr(self, target)
        r = target(*args, **kwargs)
        if not isinstance(r, BotInternalCallResult):
            raise TypeError(f'target result is not a {BotInternalCallResult.__name__} object')
        if r.ok:
            return True
        else:
            return False

    def __remove_finished_update__(self, update: Update):
        self.__saved_updates__.remove(update)

    @contextlib.contextmanager
    def __ctx_update__(self, update: Update):
        self.__dump_persistence__()
        yield
        self.__dump_persistence__()
