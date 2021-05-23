#!/usr/bin/env python3
from mylib.easy import *
from mylib.easy import logging


class FFmpegCLIArgs(CLIArgumentsList):
    merge_option_nargs = False

    @staticmethod
    def _spec_convert_keyword_to_option_name(keyword):
        return '-' + keyword.replace('___', '-').replace('__', ':')


class Error(Exception):
    def __init__(self, exit_code: int, stderr_content: str):
        self.exit_code = exit_code
        self.stderr_lines = stderr_content.splitlines()
        self.cause = None, None, None
        for es in self.stderr_lines:
            if es.startswith('Unknown encoder'):
                self.cause = 'encoder', 'unknown', es[17:-1]
            elif 'Error loading plugins' in es:
                self.cause = 'plugin', 'load', None


class FFmpegCommand:
    def __init__(self, path='ffmpeg', banner: bool = True, loglevel: str = None, overwrite: bool = ...):
        self.head = FFmpegCLIArgs(path, hide_banner=not banner, loglevel=loglevel)
        if overwrite is True:
            self.head.add(y=True)
        if overwrite is False:
            self.head.add(n=True)
        self.input_list = []
        self.output_list = []

    def add_input(self, input_url, **kwargs):
        self.input_list.append(FFmpegCLIArgs(**kwargs).add(i=input_url))
        return self

    def add_output(self, output_url, **kwargs):
        self.output_list.append(FFmpegCLIArgs(**kwargs).add(output_url))
        return self

    def build(self):
        cmd = FFmpegCLIArgs(*self.head)
        for i in self.input_list:
            cmd.add(*i)
        for o in self.output_list:
            cmd.add(*o)
        return cmd


def concat_simple(src_list, output_url):
    concat_lines = [f"file '{i}'" for i in src_list]
    concat_lines.insert(0, f'# auto generated ffmpeg concat list by {__name__}.{concat_simple.__name__}')
    concat_info = '\n'.join(concat_lines)
    if output_url is ...:
        dirname_set = {path_dirname(i) for i in src_list}
        basename_prefix = path_common_prefix([path_basename(i) for i in src_list])
        ext_set = {os.path.splitext(i)[1] for i in src_list}
        if not len(dirname_set) == 1 or not basename_prefix or not len(ext_set):
            raise ValueError('cannot guess a valid output url')
        output_url = path_join(dirname_set.pop(), f'{basename_prefix.strip()}{ext_set.pop()}')
    print(concat_info)
    cmd = FFmpegCommand(). \
        add_input('-', f='concat', safe=0, protocol_whitelist='file,pipe'). \
        add_output(output_url, c='copy'). \
        build()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(concat_info.encode())
