#!/usr/bin/env python3
# encoding=utf8
import argparse
import os
import re
import shlex
import subprocess
import time
import traceback
from pprint import pformat

from telegram.ext import MessageHandler, Filters, CallbackContext

from mylib.log import get_logger
from mylib.os_xp import monitor_sub_process_tty_frozen, ProcessTTYFrozen
from mylib.fs import read_json_file, write_json_file, read_sqlite_dict_file, write_sqlite_dict_file
from mylib.text import decode
from mylib.tg_bot import SimpleBot, deco_factory_bot_handler_method, CommandHandler, Update
from mylib.cli import new_argument_parser
from mylib.tricks_ez import deco_factory_retry

mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(os.path.realpath(__file__))))


@deco_factory_retry(retry_exceptions=ProcessTTYFrozen, max_retries=-1)
def bldl_retry_frozen(*args: str):
    p = subprocess.Popen(['bldl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8')


@deco_factory_retry(retry_exceptions=ProcessTTYFrozen, max_retries=-1)
def ytdl_retry_frozen(*args: str):
    p = subprocess.Popen(['ytdl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


def line2args(line: str):
    args = shlex.split(line.strip())
    if args[0] in '+-*!':
        args.pop(0)
    return args


class MyAssistantBot(SimpleBot):
    def __init__(self, conf_file: str, **kwargs):
        self._conf_file = conf_file
        config = read_json_file(conf_file)
        data_file = os.path.splitext(conf_file)[0] + '.db'
        self._data_file = data_file
        data = read_sqlite_dict_file(data_file, with_dill=True)
        super().__init__(token=config['token'], whitelist=config.get('user_whitelist'), data=data, **kwargs)

    def __get_conf__(self):
        return read_json_file(self._conf_file)

    def __set_conf__(self, **kwargs):
        conf = self.__get_conf__()
        conf.update(kwargs)
        write_json_file(self._conf_file, conf, indent=4)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(
        re.compile(r'BV[\da-zA-Z]{10}|av\d+')))
    def _bldl(self, update, *args):
        args_l = [line2args(line) for line in update.message.text.splitlines()]
        for args in args_l:
            args_s = ' '.join([shlex.quote(a) for a in args])
            try:
                self.__reply_md_code_block__(f'+ {args_s}', update)
                p, out, err = bldl_retry_frozen(*args)
                if p.returncode:
                    echo = ''.join([decode(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-5:]])
                    self.__requeue_failed_update__(update)
                    self.__reply_md_code_block__(f'- {args_s}\n{echo}', update)
                else:
                    echo = ''.join([s for s in [decode(b) for b in out.readlines()] if '─┤' not in s])
                    self.__reply_md_code_block__(f'* {args_s}\n{echo}', update)
            except Exception as e:
                self.__reply_md_code_block__(f'! {args_s}\n{str(e)}\n{repr(e)}', update)
                self.__requeue_failed_update__(update)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(
        re.compile(r'youtube|youtu\.be|iwara|pornhub')))
    def _ytdl(self, update: Update, *args):
        undone = self.__data__['undone']
        undone[self._ytdl.__name__] = update
        try:
            self.__save_data__()
        except Exception:
            self.__reply_md_code_block__(f'{traceback.format_exc()}', update)

        args_l = [line2args(line) for line in update.message.text.splitlines()]
        for args in args_l:
            args_s = ' '.join([shlex.quote(a) for a in args])
            try:
                self.__reply_md_code_block__(f'+ {args_s}', update)
                p, out, err = ytdl_retry_frozen(*args)
                echo = ''.join([re.sub(r'.*\[download]', '[download]', decode(b).rsplit('\r', maxsplit=1)[-1]) for b in
                                out.readlines()[-10:]])
                if p.returncode:
                    abandon_errors = self.__get_conf__().get('abandon_errors') or []
                    if any(map(lambda x: x in echo, abandon_errors)):
                        self.__reply_md_code_block__(f'- {args_s}\n{echo}', update)
                        continue
                    self.__reply_md_code_block__(f'! {args_s}\n{echo}', update)
                    self.__requeue_failed_update__(update)
                else:
                    self.__reply_md_code_block__(f'* {args_s}\n{echo}', update)
            except Exception as e:
                self.__reply_md_code_block__(f'! {args_s}\n{str(e)}\n{repr(e)}', update)
                self.__requeue_failed_update__(update)

        del undone[self._ytdl.__name__]
        try:
            self.__save_data__()
        except Exception:
            self.__reply_md_code_block__(f'{traceback.format_exc()}', update)

    @deco_factory_bot_handler_method(CommandHandler)
    def _secret(self, update: Update, *args):
        self.__typing__(update)
        for name in ('effective_message', 'effective_user'):
            self.__reply_md_code_block__(f'{name}\n{pformat(getattr(update, name).to_dict())}', update)
        self.__reply_md_code_block__(f'bot.get_me()\n{pformat(self.__bot__.get_me().to_dict())}', update)

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True, pass_args=True)
    def sleep(self, u: Update, c: CallbackContext):
        """sleep some time (unit: sec)"""
        args = c.args or [0]
        t = float(args[0])
        self.__reply_text__(f'sleep {t} seconds', u)
        time.sleep(t)
        self.__reply_text__('awake...', u)

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True, pass_args=True)
    def errors(self, u: Update, c: CallbackContext):
        """manage subprocess errors"""
        args = c.args
        if not args:
            usage_s = '/errors {+,-,:} [T]'
            self.__reply_md_code_block__(usage_s, u)
            return
        arg0, arg1 = args[0], ' '.join(args[1:])
        errors = self.__get_conf__().get('abandon_errors', [])
        if arg0 == ':':
            self.__reply_md_code_block__(pformat(errors), u)
        elif arg0 == '+':
            errors = sorted(set(errors) | {arg1})
            self.__set_conf__(abandon_errors=errors)
            self.__reply_md_code_block__(pformat(errors), u)
        elif arg0 == '-':
            errors = sorted(set(errors) - {arg1})
            self.__set_conf__(abandon_errors=errors)
            self.__reply_md_code_block__(pformat(errors), u)
        else:
            self.__reply_md_code_block__(pformat(errors), u)

    def __save_data__(self, data_file_path=None):
        data_file_path = data_file_path or self._data_file
        self.__data__['queued'] = list(self.__updater__.dispatcher.update_queue.queue)
        super().__save_data__(data_file_path)


def main():
    ap = new_argument_parser()
    ap.add_argument('-c', '--config-file', metavar='path', required=True)
    ap.add_argument('-v', '--verbose', action='store_true')
    ap.add_argument('-T', '--timeout', type=float)
    parsed_args = ap.parse_args()
    config_file = parsed_args.config_file
    timeout = parsed_args.timeout

    if parsed_args.verbose:
        log_lvl = 'DEBUG'
        print(parsed_args)
    else:
        log_lvl = 'INFO'
    get_logger('telegram').setLevel(log_lvl)
    bot = MyAssistantBot(config_file, timeout=timeout, auto_run=False)
    bot.__run__()


if __name__ == '__main__':
    # ensure_sigint_signal()
    main()
