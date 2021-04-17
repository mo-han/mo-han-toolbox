#!/usr/bin/env python3
# encoding=utf8
import i18n
from mylib.easy import *

load_path = i18n.load_path
tt = i18n.t


def insert_load_dir(path: str = 'i18n', index=0):
    load_path.insert(index, path)


def remove_namespace_from_filename_format():
    i18n.set('filename_format', '{locale}.{format}')


def map_locale_to_rfc5646___alpha(the_locale: str):
    """RFC 5646"""
    d = {'zh-cn': 'zh-Hans', 'zh-hk': 'zh-Hant', 'zh-tw': 'zh-Hant'}
    the_locale = the_locale.replace('_', '-').lower()
    return d.get(the_locale, the_locale.split('-')[0])


def set_locale(the_locale: str = get_os_default_lang()):
    i18n.config.set('locale', map_locale_to_rfc5646___alpha(the_locale))


def enable_memoization():
    i18n.set('enable_memoization', True)


def preset_alpha():
    remove_namespace_from_filename_format()
    insert_load_dir()
    set_locale()
