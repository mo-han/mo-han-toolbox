#!/usr/bin/env python3
# encoding=utf8
import argparse
import os
import re
import subprocess
import time
from pprint import pformat

from mylib.log import get_logger
from mylib.os_util import read_json_file, monitor_sub_process_tty_frozen
from mylib.text import decode
from mylib.tricks import ArgParseCompactHelpFormatter, meta_deco_retry

ap = argparse.ArgumentParser(formatter_class=ArgParseCompactHelpFormatter)
ap.add_argument('-c', '--config-file', metavar='path', required=True)
ap.add_argument('-v', '--verbose', action='store_true')
ap.add_argument('-T', '--timeout', type=float)
parsed_args = ap.parse_args()
config_file = parsed_args.config_file
config = read_json_file(config_file)
update_queue_file = os.path.splitext(config_file)[0] + '.dat'
mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(os.path.realpath(__file__))))


@meta_deco_retry(retry_exceptions=TimeoutError, max_retries=-1)
def bldl_retry_frozen(*args: str):
    p = subprocess.Popen(['bldl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8')


@meta_deco_retry(retry_exceptions=TimeoutError, max_retries=-1)
def ytdl_retry_frozen(*args: str):
    p = subprocess.Popen(['ytdl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


def main():
    from mylib.tg_bot import SimpleBot, meta_deco_handler_method, CommandHandler, Update
    from telegram.ext import MessageHandler, Filters, CallbackContext
    from mylib.bili import find_bilibili_vid

    class MyAssistantBot(SimpleBot):
        @meta_deco_handler_method(MessageHandler, filters=Filters.regex(
            re.compile(r'BV[\da-zA-Z]{10}|av\d+')))
        def _bldl(self, update, *args):
            args = [s.strip() for s in update.message.text.splitlines()]
            vid = find_bilibili_vid(args[0])
            args[0] = vid
            args_str = ' '.join(args)
            try:
                self.__reply_md_code_block__(f'+ {args_str}', update)
                p, out, err = bldl_retry_frozen(*args)
                if p.returncode:
                    echo = ''.join([decode(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-5:]])
                    self.__reply_md_code_block__(f'- {args_str}\n{echo}', update)
                else:
                    echo = ''.join([s for s in [decode(b) for b in out.readlines()] if '─┤' not in s])
                    self.__reply_md_code_block__(f'* {args_str}\n{echo}', update)
            except Exception as e:
                e_repr = repr(e)
                self.__reply_md_code_block__(f'! {args_str}\n{e_repr}', update)

        @meta_deco_handler_method(MessageHandler, filters=Filters.regex(
            re.compile(r'youtube|youtu\.be|iwara|pornhub')))
        def _ytdl(self, update: Update, *args):
            args = [s.strip() for s in update.message.text.splitlines()]
            args[0] = re.findall(r'https?://.+', args[0])[0]
            args_str = ' '.join(args)
            try:
                self.__reply_md_code_block__(f'+ {args_str}', update)
                p, out, err = ytdl_retry_frozen(*args)
                while 1:
                    if p.returncode:
                        echo = ''.join([decode(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-10:]])
                        self.__reply_md_code_block__(f'- {args_str}\n{echo}', update)
                        if 'ERROR: ' in echo:
                            break
                        p, out, err = ytdl_retry_frozen(*args)
                    else:
                        echo = ''.join([s for s in [decode(b) for b in out.readlines()[-10:]]])
                        self.__reply_md_code_block__(f'* {args_str}\n{echo}', update)
                        break
            except Exception as e:
                e_repr = repr(e)
                self.__reply_md_code_block__(f'! {args_str}\n{e_repr}', update)

        @meta_deco_handler_method(CommandHandler)
        def _secret(self, update: Update, *args):
            self.__typing__(update)
            for name in ('effective_message', 'effective_user'):
                self.__reply_md_code_block__(f'{name}\n{pformat(getattr(update, name).to_dict())}', update)
            self.__reply_md_code_block__(f'bot.get_me()\n{pformat(self.bot.get_me().to_dict())}', update)

        def __about_this_bot__(self):
            return f'{super().__about_this_bot__()}\n\n' \
                   f'script modified time:\n' \
                   f'{mt}'

        @meta_deco_handler_method(CommandHandler, on_menu=True, pass_args=True)
        def sleep(self, u: Update, c: CallbackContext):
            """sleep some time (unit: sec)"""
            args = c.args or [0]
            t = float(args[0])
            self.__reply_text__(f'sleep {t} seconds', u)
            time.sleep(t)
            self.__reply_text__('awoken!', u)

    if parsed_args.verbose:
        log_lvl = 'DEBUG'
        print(parsed_args)
        print(config)
    else:
        log_lvl = 'INFO'
    get_logger('telegram').setLevel(log_lvl)
    token = config['token']
    bot = MyAssistantBot(token, whitelist=config.get('user_whitelist'), timeout=parsed_args.timeout, auto_run=False)
    bot.__run__()


if __name__ == '__main__':
    # ensure_sigint_signal()
    main()
