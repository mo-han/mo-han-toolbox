#!/usr/bin/env python3
# encoding=utf8
import os
import re
import argparse

from telegram.ext import MessageHandler, Filters

from mylib.bilibili import find_bilibili_vid
from mylib.log import get_logger
from mylib.os_util import read_json_file
from mylib.tg_bot import SimpleBot, meta_deco_handler_method

get_logger('telegram').setLevel('INFO')


class MyAssistantBot(SimpleBot):
    @meta_deco_handler_method(MessageHandler, filters=Filters.regex(
        re.compile(r'BV[\da-zA-Z]{10}|av\d+|bilibili|b23\.tv')))
    def bilibili_video(self, update, context):
        program = 'bldl'
        vid = find_bilibili_vid(update.message.text)
        cmd = f'{program} {vid}'
        update.message.reply_text(f'+ {vid}')
        os.system(cmd)
        update.message.reply_text(f'* {vid}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-c', '--config-file')
    args = ap.parse_args()
    config_file = args.config_file
    config = read_json_file(config_file)
    token = config['token']
    bot = MyAssistantBot(token, user_whitelist=config.get('user_whitelist'))
