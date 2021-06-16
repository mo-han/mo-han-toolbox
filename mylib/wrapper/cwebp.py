#!/usr/bin/env python3
import enum
import math
from functools import partial

from PIL import Image

from mylib.ex.PIL import open_bytes_as_image, save_image_to_bytes
from mylib.easy import *
from mylib.easy import logging

logger = logging.get_logger(__name__)


class CWebpCLIArgs(CLIArgumentsList):
    merge_option_nargs = True

    @staticmethod
    def _spec_convert_keyword_to_option_name(keyword):
        return '-' + keyword


def new_cwebp_cmd():
    return CWebpCLIArgs('cwebp')


def cwebp_call(src: T.Union[str, bytes], dst: T.Union[str, bool, T.NoneType, T.EllipsisType] = ..., **kwargs):
    if isinstance(src, str):
        src_bytes = None
        src_size = os.path.getsize(src)
    elif isinstance(src, bytes):
        src_bytes = src
        src = '-'
        src_size = len(src_bytes)
    else:
        raise TypeError('src', (str, bytes))
    src_data = {'path': src, 'size': src_size}

    if dst is ...:
        dst = src + '.webp'

    dst_data = {}
    if 'q' in kwargs:
        dst_data['q'] = float(kwargs['q'])

    resize = kwargs.pop('resize', None)
    if isinstance(resize, (int, float)) and resize > 0 and resize != 1:
        # resize = round(resize, 2)
        if src_bytes is None:
            src_img = Image.open(src)
        else:
            src_img = open_bytes_as_image(src_bytes)
        w, h = src_img.size
        kwargs['resize'] = round(w * resize), round(h * resize)
        src_data['width'] = w
        src_data['height'] = h
        dst_data['scale'] = resize

    cmd = new_cwebp_cmd().add(**kwargs).add(o=dst).add('--', src)
    p = subprocess.run(cmd, input=src_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    encoding = get_os_default_encoding()
    msg_lines = p.stderr.decode(encoding).splitlines()
    ok = p.returncode == 0
    rj = {
        'kwargs': kwargs,
        'out': p.stdout,
        'msg': msg_lines,
        'cmd': p.args,
        'code': p.returncode,
        'ok': ok,
        'src': src_data,
    }
    if ok:
        if dst:
            dst_data['path'] = dst
        if len(msg_lines) == 1:
            line = msg_lines[0]
            size, psnr = line.strip().split()
            dst_data.update({'size': int(size), 'psnr': {'all': float(psnr)}})
        elif msg_lines:
            for line in msg_lines:
                if line.startswith('Dimension:'):
                    values = [int(s) for s in re.findall(r'\d+', line)]
                    keys = ('width', 'height')
                    dst_data.update({k: v for k, v in zip(keys, values)})
                    break
            for line in msg_lines:
                if line.startswith('Output:'):
                    size_and_4_psnr = re.findall(r'[\d.]+', line)
                    size = size_and_4_psnr[0]
                    psnr_v = size_and_4_psnr[1:]
                    psnr_k = ('y', 'u', 'v', 'all')
                    dst_data.update({
                        'size': int(size),
                        'psnr': {k: float(v) for k, v in zip(psnr_k, psnr_v)}
                    })
                    break
            for line in msg_lines:
                if line.startswith('LSIM:') or line.startswith('SSIM:'):
                    segments = line.lower().split()
                    name = segments.pop(0).split(':')[0]
                    dst_data[name] = {left: float(right) for left, right in [seg.split(':') for seg in segments]}
        dst_data['compress'] = round(dst_data['size'] / src_data['size'], 3)
        rj['dst'] = dst_data
    return rj


def cwebp(src: T.Union[str, bytes], dst: T.Union[str, bool, T.NoneType, T.EllipsisType] = ..., **kwargs):
    try:
        return check_cwebp_call_result(cwebp_call(src, dst, **kwargs))
    except CWebpInputReadError:
        if 'Corrupt JPEG data: premature end of data segment' in cwebp_call(src, dst, **kwargs)['msg']:
            if isinstance(src, bytes):
                img = open_bytes_as_image(src)
            else:
                img = Image.open(src)
            return check_cwebp_call_result(cwebp_call(save_image_to_bytes(img, dst, **kwargs)))


def cwebp_help_text():
    return subprocess.run(new_cwebp_cmd().add(longhelp=True), stdout=subprocess.PIPE).stdout.decode()


class SkipOverException(Exception):
    def __init__(self, msg):
        self.msg = msg


class CWebpGenericError(ChildProcessError):
    pass


class CWebpEncodeError(CWebpGenericError):
    class E(metaclass=AttrConstEllipsisForStringMetaClass):
        BAD_DIMENSION = ...

    def __init__(self, code: int, reason: str, desc: str):
        self.code = code
        self.reason = reason
        self.desc = desc
        super().__init__(code, f'{reason}: {desc}')


class CWebpInputReadError(CWebpGenericError):
    pass


def check_cwebp_call_result(result: dict):
    if not result['ok']:
        msg_lines = result['msg']
        r_code = result['code']
        if msg_lines[0].startswith('Error! '):
            raise CWebpGenericError(r_code, msg_lines[0][7:])
        if msg_lines[1] == 'Error! Cannot encode picture as WebP':
            m = re.match(r'Error code: (?P<code>\d+) \((?P<reason>\w+): (?P<desc>.+)\)', msg_lines[2])
            if m:
                code, reason, desc = m.groups()
                raise CWebpEncodeError(code=code, reason=reason, desc=desc)
        if any(map(
                lambda x: any(map(x.startswith, ('Input file read error', 'Error! Cannot read input picture file'))),
                msg_lines)):
            raise CWebpInputReadError(r_code, msg_lines)
        raise CWebpGenericError(r_code, msg_lines)
    return result


def cwebp_adaptive_gen___alpha(src, max_size: int, max_compress: float, max_q: int, min_q: int, min_scale: float,
                               *, q_step=5, scale_step=0.05):
    q_step_by_100 = q_step / 100

    _cwebp = partial(cwebp, src, '-')

    def calc_dst_size_compress_divided_by_max(cwebp_data: dict):
        o_size = cwebp_data['dst']['size']
        o_compress = cwebp_data['dst']['compress']
        return o_size / max_size, o_compress / max_compress

    scale = min_scale
    q = min_q
    d = _cwebp(resize=scale, q=q)
    yield d
    size_by_max, compress_by_max = calc_dst_size_compress_divided_by_max(d)
    if size_by_max > 1 or compress_by_max > 1:
        if max_size / d['src']['size'] > max_compress:
            raise SkipOverException('modest file size, keep original')
        else:
            yield _cwebp(resize=scale, size=max_size)
            return

    q += min(int((1 - size_by_max) / q_step_by_100), int((1 - compress_by_max) / q_step_by_100)) * q_step
    q = min(max_q, q)
    logger.debug(f'estimate q: {q}')
    if q == min_q and scale == 1:
        return

    while q >= min_q:
        scale = 1
        d = _cwebp(resize=scale, q=q)
        yield d
        size_by_max, compress_by_max = calc_dst_size_compress_divided_by_max(d)
        if size_by_max <= 1 and compress_by_max <= 1:
            return

        if size_by_max > 1:
            scale = round_to(int(scale / math.sqrt(size_by_max) / scale_step) * scale_step, scale_step)
        else:
            scale = round_to(int(scale / math.sqrt(compress_by_max) / scale_step) * scale_step, scale_step)
        logger.debug(f'estimate scale: {scale}')
        if scale < min_scale:
            q -= q_step
            logger.debug(f'reduce q to: {q}')
            continue

        while scale >= min_scale:
            d = _cwebp(resize=scale, q=q)
            yield d
            size_by_max, compress_by_max = calc_dst_size_compress_divided_by_max(d)
            if size_by_max <= 1 and compress_by_max <= 1:
                return
            if size_by_max > 1:
                scale = round_to(int(scale / math.sqrt(size_by_max) / scale_step) * scale_step, scale_step)
            else:
                scale = round_to(int(scale / math.sqrt(compress_by_max) / scale_step) * scale_step, scale_step)
            logger.debug(f'estimate scale: {scale}')
        else:
            q -= q_step

    else:
        yield _cwebp(resize=scale, size=max_size)
        return
