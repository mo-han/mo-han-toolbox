#!/usr/bin/env python3
from ast import literal_eval

import webptools
import subprocess
from mylib.ez import *


class CLIArgs(CLIArgumentsList):
    @staticmethod
    def keyword_to_option_name(keyword):
        return '-' + keyword


def make_cwebp_argv(src: str, dst: str, **kwargs):
    return CLIArgs(webptools.webplib.getcwebp(), **kwargs).add(src, o=dst)


def cwebp(src: str, dst: str or False or Ellipsis = ..., **kwargs):
    if dst is ...:
        dst = src + '.webp'
    argv = make_cwebp_argv(src, dst, **kwargs)
    r = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    encoding = get_default_encoding()
    stdout_lines = r.stdout.decode(encoding).splitlines()
    stderr_lines = r.stderr.decode(encoding).splitlines()
    d = {
        'input': {'path': src},
        'args': r.args,
        'code': r.returncode,
        'stdout': stdout_lines,
        'stderr': stderr_lines,
    }
    ok = r.returncode == 0
    if ok:
        output = {}
        if dst:
            output['path'] = dst
        if len(stderr_lines) == 1:
            line = stderr_lines[0]
            size, psnr = line.strip().split()
            output.update({'size': int(size), 'psnr': {'all': float(psnr)}})
        elif stderr_lines:
            for line in stderr_lines:
                if line.startswith('Dimension:'):
                    values = [int(s) for s in re.findall(r'\d+', line)]
                    keys = ('width', 'height')
                    output.update({k: v for k, v in zip(keys, values)})
                    break
            for line in stderr_lines:
                if line.startswith('Output:'):
                    size_and_4_psnr = re.findall(r'[\d.]+', line)
                    size = size_and_4_psnr[0]
                    psnr_v = size_and_4_psnr[1:]
                    psnr_k = ('y', 'u', 'v', 'all')
                    output.update({
                        'size': int(size),
                        'psnr': {k: v for k, v in zip(psnr_k, psnr_v)}
                    })
                    break
        d['output'] = output
    return d
