#!/usr/bin/env python3
import i18n as python_i18n
import yaml

from mylib.easy import get_os_default_lang, functools

SEP_KEY = '__separator__'

load_path: list = python_i18n.load_path
records = {}


def translate_and_record(key, **kwargs):
    try:
        r = python_i18n.t(key, **kwargs)
        v = None if r == key else r
    except TypeError:
        r = key
        v = None
    records[key] = v
    return r


@functools.lru_cache()
def cached_translate(key, **kwargs):
    return translate_and_record(key, **kwargs)


def dump_records_to_yaml_source_file___pre_alpha(fp: str, null_as_blank=True, unicode=True, **kwargs):
    encoding = 'utf-8'
    old = yaml.safe_load(open(fp, encoding=encoding).read())
    for k in old.keys():
        v: dict = old[k]
        v.update(records)
        old[k] = dict(sorted(v.items()))
    s = yaml.safe_dump(old, allow_unicode=unicode, **kwargs)
    if null_as_blank:
        s = s.replace(': null\n', ':\n')
    with open(fp, 'w', encoding=encoding) as f:
        f.write(s)


def get_separator(default=' ') -> str:
    sep = translate_and_record(SEP_KEY)
    return default if sep == SEP_KEY else sep


def join(*args):
    sep = get_separator()
    return sep.join(args)


def insert_load_dir(path: str = 'i18n', index=0):
    load_path.insert(index, path)


def remove_namespace_from_filename_format():
    python_i18n.set('filename_format', '{locale}.{format}')


def map_locale_to_rfc5646___alpha(the_locale: str):
    """RFC 5646"""
    d = {'zh-cn': 'zh-Hans', 'zh-hk': 'zh-Hant', 'zh-tw': 'zh-Hant'}
    the_locale = the_locale.replace('_', '-').lower()
    return d.get(the_locale, the_locale.split('-')[0])


def set_locale(the_locale: str = get_os_default_lang()):
    python_i18n.config.set('locale', map_locale_to_rfc5646___alpha(the_locale))


def get_locale():
    return python_i18n.config.get('locale')


def reload_all():
    for p in load_path:
        python_i18n.resource_loader.load_directory(p, locale=get_locale())


def enable_memoization():
    python_i18n.set('enable_memoization', True)


def disable_memoization():
    python_i18n.set('enable_memoization', False)


def preset___alpha():
    remove_namespace_from_filename_format()
    insert_load_dir()
    set_locale()
