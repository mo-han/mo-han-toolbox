#!/usr/bin/env python3
import imghdr
import traceback
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

import PIL.Image
from send2trash import send2trash

from mylib import fstk
from mylib import ostk
from mylib.ez import *
from mylib.ez import argparse
from mylib.wrapper import cwebp
from mylib.tui import LinePrinter
from humanize import naturaldelta

PIXELS_BASELINE = 1280 * 1920
MAX_Q = 80
MIN_Q = 50
MAX_COMPRESS = 0.667

apr = argparse.ArgumentParserRigger()
an = apr.an
lp = LinePrinter()


class Counter:
    n = 0


def convert_adaptive(image_fp, counter: Counter = None):
    webp_fp = image_fp + '.webp'
    what = imghdr.what(image_fp)
    if not what or what in ('webp', 'gif'):
        print(f'# skip {image_fp}')
        return
    if counter:
        counter.n += 1
    img: PIL.Image.Image = PIL.Image.open(image_fp)
    w, h = img.size
    pixels = w * h
    if pixels > PIXELS_BASELINE * 4:
        max_size = 1024 * 1024
        min_scale = 0.7
    elif pixels > PIXELS_BASELINE * 3:
        max_size = 1024 * 768
        min_scale = 0.8
    elif pixels > PIXELS_BASELINE * 2:
        max_size = 1024 * 768
        min_scale = 0.9
    elif pixels > PIXELS_BASELINE:
        max_size = 1024 * 512
        min_scale = 1
    else:
        max_size = 1024 * 384
        min_scale = 1
    print(f'+ ({w}x{h}, q={MAX_Q}..{MIN_Q}, min_scale={min_scale}, '
          f'max_size={max_size}, max_compress={MAX_COMPRESS}) {image_fp}')
    try:
        with open(image_fp, 'rb') as fd:
            image_file_bytes = fd.read()
        for result in cwebp.cwebp_adaptive_iter___alpha(
                image_file_bytes, max_size=max_size, max_compress=MAX_COMPRESS,
                max_q=MAX_Q, min_q=MIN_Q, min_scale=min_scale):
            d = cwebp.check_cwebp_subprocess_result(result)
            d_dst = d['dst']
            print(f"* ({d_dst['width']}x{d_dst['height']}, q={d_dst.get('q', '?')}, scale={d_dst.get('scale', 1)}, "
                  f"size={d_dst['size']}, compress={d_dst['compress']}, psnr={d_dst['psnr']['all']}) <- {image_fp}")
        with open(webp_fp, 'wb') as f:
            f.write(d['out'])
    except cwebp.SkipOverException as e:
        print(f'# ({e.msg}) {image_fp}')
    except KeyError as e:
        print(traceback.format_exc())
        print(f'! {image_fp}')
        if e.args[0] == 'dst':
            pprint(d)
        os_exit_force(1)
    except Exception:
        print(traceback.format_exc())
        print(f'! {image_fp}')
        os_exit_force(1)


@apr.sub(apr.rename_factory_replace_underscore())
@apr.true('R', 'recursive')
@apr.true('L', 'clean')
@apr.true('C', 'cbz')
@apr.arg('src', nargs='*')
@apr.map('src', recursive='recursive', clean='clean', cbz='cbz')
def batch(src, recursive, clean, cbz):
    if not src:
        src = ostk.clipboard.list_path()
    ostk.ensure_sigint_signal()
    cnt = Counter()
    t0 = time.time()
    for s in src:
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            for fp in fstk.find_iter('f', s, recursive=recursive):
                executor.submit(convert_adaptive, fp, counter=cnt)
        if clean:
            for fp in fstk.find_iter('f', s, recursive=recursive):
                ext_lower = os.path.splitext(fp)[-1].lower()
                fp_webp = fp + '.webp'
                if ext_lower != '.webp' and os.path.isfile(fp_webp) and os.path.getsize(fp_webp):
                    send2trash(fp)
                    print(f'- {fp}')
                    continue
                if ext_lower == '.thumb':
                    send2trash(fp)
                    print(f'- {fp}')
                    continue
        if cbz:
            if os.path.isdir(s):
                dirs_containing_webp = []
                for dp, sub_dirs, files in os.walk(s):
                    if any([f.endswith('.webp') for f in files]):
                        dirs_containing_webp.append(dp)
                for dp in dirs_containing_webp:
                    cbz_fp = dp + '.cbz'
                    try:
                        fstk.make_zipfile_from_dir(cbz_fp, dp)
                    except NotADirectoryError:
                        print(f'! {dp}')
                    print(f'+ {cbz_fp} <- {dp}')
                    send2trash(dp)
                    print(f'- {dp}')
    t = time.time() - t0
    n = cnt.n
    lp.l()
    print(f'{n} images in {naturaldelta(t)}, {naturaldelta(t / n)} per image')


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
