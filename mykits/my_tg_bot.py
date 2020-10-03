#!/usr/bin/env python3
# encoding=utf8
import argparse
import locale
import re
import subprocess
from pprint import pformat

from mylib.log import get_logger
from mylib.os_util import read_json_file, ensure_sigint_signal, monitor_sub_process_tty_frozen
from mylib.tricks import ArgParseCompactHelpFormatter, meta_deco_retry
from mylib.text import decode

ap = argparse.ArgumentParser(formatter_class=ArgParseCompactHelpFormatter)
ap.add_argument('-c', '--config-file', metavar='path', required=True)
ap.add_argument('-v', '--verbose', action='store_true')
ap.add_argument('-T', '--timeout', type=float)
args = ap.parse_args()
config_file = args.config_file
config = read_json_file(config_file)


@meta_deco_retry(exceptions=TimeoutError, max_retries=-1)
def bldl_retry_frozen(vid):
    p = subprocess.Popen(['bldl.cmd', str(vid)], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8')


def main():
    from telegram.ext import MessageHandler, Filters
    from mylib.bili import find_bilibili_vid
    from mylib.tg_bot import SimpleBot, meta_deco_handler_method, CommandHandler, Update

    class MyAssistantBot(SimpleBot):
        @meta_deco_handler_method(MessageHandler, filters=Filters.regex(
            re.compile(r'BV[\da-zA-Z]{10}|av\d+|bilibili|b23\.tv')))
        def bldl(self, update, context):
            vid = find_bilibili_vid(update.message.text)
            try:
                update.message.reply_text(f'+ {vid}')
                p, out, err = bldl_retry_frozen(vid)
                if p.returncode:
                    update.message.reply_text(f'- {vid}')
                    echo = ''.join([decode(b) for b in out.readlines()[-3:]])
                    self.__reply_markdown__(update, f'```\n{echo}```')
                else:
                    update.message.reply_text(f'* {vid}')
                    echo = ''.join([decode(b) for b in out.readlines()])
                    self.__reply_markdown__(update, f'```\n{echo}```')
            except Exception as e:
                update.message.reply_text(f'! {vid}')
                self.__reply_markdown__(update, f'```{repr(e)}```')

        @meta_deco_handler_method(CommandHandler)
        def _secret(self, update: Update, context):
            self.__typing__(update)
            for name in ('effective_message', 'effective_user'):
                update.message.reply_text(name)
                update.message.reply_text(pformat(getattr(update, name).to_dict()))
            update.message.reply_text('bot.get_me()')
            update.message.reply_text(pformat(self.bot.get_me().to_dict()))

    if args.verbose:
        log_lvl = 'DEBUG'
        print(args)
        print(config)
    else:
        log_lvl = 'INFO'
    get_logger('telegram').setLevel(log_lvl)
    token = config['token']
    MyAssistantBot(token, user_whitelist=config.get('user_whitelist'), timeout=args.timeout)


if __name__ == '__main__':
    ensure_sigint_signal()
    main()
