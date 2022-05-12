#!/usr/bin/env python3
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

import PIL.Image
import chardet
import filetype
from humanize import naturaldelta, naturalsize
from send2trash import send2trash

import ezpykit.stdlib.os.common
import ezpykit.stdlib.shutil.__deprecated__
from mylib.easy import logging
from mylib.ext.console_app import *
from mylib.wrapper import cwebp

PIXELS_BASELINE = 1280 * 1920
MAX_Q = 80
MIN_Q = 50
MAX_COMPRESS = 0.667

apr = ArgumentParserWrapper()
an = apr.an
cpr = ConsolePrinter()
an.B = an.trash_bin = an.src = an.file = an.x = an.extension = an.w = an.workdir = an.v = an.verbose = ''
an.T = an.strict = ''


class Counter:
    n = 0


def convert_adaptive(image_fp, counter: Counter = None, print_path_relative_to=None):
    if print_path_relative_to:
        image_fp_rel = fstk.make_path(image_fp, relative_to=print_path_relative_to)
        if image_fp_rel == '.':
            image_fp_rel = image_fp
    else:
        image_fp_rel = image_fp
    webp_fp = image_fp + '.webp'
    mime_type, mime_sub = (filetype.guess_mime(image_fp) or '/').split('/')
    if mime_type != 'image':
        print(f'# skip non-image {image_fp_rel}')
        return
    if mime_sub in {'webp', 'gif'}:
        print(f'# skip {mime_sub} image {image_fp_rel}')
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
        max_size = 1024 * 512
        min_scale = 0.9
    elif pixels > PIXELS_BASELINE:
        max_size = 1024 * 384
        min_scale = 1
    else:
        max_size = 1024 * 256
        min_scale = 1
    print(f'+ ({w}x{h}, q={MAX_Q}..{MIN_Q}, min_scale={min_scale}, '
          f'max_size={max_size}, max_compress={MAX_COMPRESS}) {image_fp_rel}')
    try:
        with open(image_fp, 'rb') as fd:
            image_file_bytes = fd.read()
        cvt_gen = cwebp.cwebp_adaptive_gen___alpha(image_file_bytes, max_size=max_size, max_compress=MAX_COMPRESS,
                                                   max_q=MAX_Q, min_q=MIN_Q, min_scale=min_scale)
        for result in cvt_gen:
            d_dst = result['dst']
            print(f"* ({d_dst['width']}x{d_dst['height']}, q={d_dst.get('q', '?')}, scale={d_dst.get('scale', 1)}, "
                  f"psnr={d_dst['psnr']['all']}, size={d_dst['size']}, compress={d_dst['compress']}) <- {image_fp_rel}")
        with open(webp_fp, 'wb') as f:
            f.write(result['out'])
    except cwebp.SkipOverException as e:
        print(f'# ({e.msg}) {image_fp_rel}')
    except KeyError as e:
        print(traceback.format_exc())
        print(f'! {image_fp_rel}')
        if e.args[0] == 'dst':
            pprint(result)
        os_exit_force(1)
    except cwebp.CWebpEncodeError as e:
        if e.reason == e.E.BAD_DIMENSION:
            print(f'! ({e.reason}) <- {image_fp_rel}')
        else:
            print(traceback.format_exc())
            print(f'! {image_fp_rel}')
            os_exit_force(1)
    except cwebp.CWebpInputReadError as e:
        print(traceback.format_exc())
        print(f'! {image_fp_rel}')
    except Exception:
        print(traceback.format_exc())
        print(f'! {image_fp_rel}')
        os_exit_force(1)


@apr.sub(apr.rpl_dot, aliases=['cvt.in.zip', 'cvt.zip'])
@apr.arg(an.src, nargs='*')
@apr.opt(an.w, an.workdir, default='.')
@apr.opt(an.x, an.extension, default='.cbz', help='file extension')
@apr.true(an.T, an.strict)
@apr.true(an.v, an.verbose)
@apr.opt('k', 'workers', type=int, metavar='N')
@apr.map(an.src, workdir=an.workdir, workers='workers', ext_name=an.extension,
         strict_mode=an.strict, verbose=an.verbose)
def convert_in_zip(src, workdir='.', workers=None, ext_name=None, strict_mode=False, verbose=False,
                   fallback_filename_encoding=get_os_default_encoding()):
    """convert non-webp picture inside zip file"""
    flag_filename_of_webp_converted = '__ALREADY_WEBP_CONVERTED__'
    lgr = logging.ez_get_logger(convert_in_zip.__name__, 'INFO' if verbose else 'ERROR',
                                fmt=logging.LOG_FMT_MESSAGE_ONLY)

    dirs, files = resolve_path_to_dirs_files(src)
    if not files:
        files = []
        [files.extend(resolve_path_to_dirs_files(path_join(dp, '**'), glob_recurse=True)[-1]) for dp in dirs]

    for fp in files:
        need_to_convert = False

        if not fstk.does_file_mime_has(fp, 'zip'):
            continue

        with zipfile.ZipFile(fp) as zf:
            if any(map(lambda x: path_basename(x) == flag_filename_of_webp_converted, zf.namelist())):
                lgr.info(f'# skip {fp}')
                continue

            possible_encodings = []
            for i in zf.infolist():
                if i.flag_bits & 0x800:  # UTF-8 filename flag
                    continue
                filename_cp437 = i.filename.encode('cp437')
                guess_encoding = chardet.detect(filename_cp437)['encoding'] or fallback_filename_encoding
                if guess_encoding.startswith('ISO-8859') or guess_encoding in ('IBM866',):
                    guess_encoding = fallback_filename_encoding
                if guess_encoding == 'ascii':
                    continue
                possible_encodings.append(guess_encoding)
            the_most_encodings = find_most_frequent_in_iterable(possible_encodings)
            # print(possible_encodings)
            # print(the_most_encodings)
            if len(the_most_encodings) == 1:
                encoding = the_most_encodings[0]
                for i in zf.infolist():
                    if i.flag_bits & 0x800:  # UTF-8 filename flag
                        continue
                    filename_cp437 = i.filename.encode('cp437')
                    i.filename = filename_cp437.decode(encoding)
                    zf.NameToInfo[i.filename] = i
            elif the_most_encodings:
                raise NotImplementedError(the_most_encodings)

            for i in zf.infolist():
                if i.is_dir():
                    continue
                with zf.open(i) as i_file_io:
                    mime = filetype.guess_mime(i_file_io.read(512))
                if mime and 'image' in mime:
                    if mime == 'image/gif':
                        continue
                    elif mime == 'image/webp':
                        need_to_convert = False
                        if strict_mode:
                            continue
                        else:
                            break
                    else:
                        need_to_convert = True
                        if strict_mode:
                            break
                        else:
                            continue

            if not need_to_convert:
                continue
            unzip_dir = path_join(workdir, split_path_dir_base_ext(fp)[1])
            try:
                zf.extractall(unzip_dir)
            except zipfile.BadZipFile:
                if path_is_dir(unzip_dir):
                    shutil.rmtree(unzip_dir)
                continue

        try:
            old_size = path_size(fp)
            auto_cvt(unzip_dir, recursive=True, clean=True, cbz=False, workers=workers, verbose=verbose)
            ezpykit.stdlib.os.common.touch(path_join(unzip_dir, flag_filename_of_webp_converted))
            new_zip = shutil.make_archive(unzip_dir, 'zip', unzip_dir, verbose=verbose)
            if ext_name:
                new_zip = fstk.rename_file_ext(new_zip, ext_name)
                fp = fstk.rename_file_ext(fp, ext_name)
            new_size = path_size(new_zip)
            fstk.move_as(new_zip, fp)
            lgr.info(fp)
            lgr.info(f'{new_size / old_size:.1%} ({naturalsize(new_size, True)} / {naturalsize(old_size, True)})')
        except KeyboardInterrupt:
            sys.exit(2)
        finally:
            shutil.rmtree(unzip_dir)


@apr.sub(apr.rpl_dot)
@apr.true('r', 'recursive')
@apr.true('c', 'clean')
@apr.true('z', 'cbz')
@apr.opt('k', 'workers', type=int, metavar='N')
@apr.true(an.B, apr.dst2opt(an.trash_bin), help='delete to trash bin')
@apr.arg('src', nargs='*')
@apr.map('src', recursive='recursive', clean='clean', cbz='cbz', workers='workers', trash_bin=an.trash_bin)
def auto_cvt(src, recursive, clean, cbz, workers=None, trash_bin=False, verbose=False):
    """convert images to webp with auto-clean, auto-compress-to-cbz, adaptive-quality-scale"""
    workers = workers or os.cpu_count() - 1 or os.cpu_count()
    lgr = logging.ez_get_logger(auto_cvt.__name__, 'INFO' if verbose else 'ERROR', fmt=logging.LOG_FMT_MESSAGE_ONLY)
    delete = send2trash if trash_bin else ezpykit.stdlib.shutil.__deprecated__.remove

    dirs, files = resolve_path_to_dirs_files(src)
    src = dirs + files
    ostk.ensure_sigint_signal()
    cnt = Counter()
    t0 = time.time()
    lgr.info(f'# workers={workers}')
    try:
        for s in src:
            lgr.info(f'@ {s}')
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for fp in fstk.find_iter('f', s, recursive=recursive):
                    executor.submit(convert_adaptive, fp, counter=cnt, print_path_relative_to=s)
            if clean:
                lgr.info('# clean already converted original image files')
                for fp in fstk.find_iter('f', s, recursive=recursive):
                    ext_lower = os.path.splitext(fp)[-1].lower()
                    fp_webp = fp + '.webp'
                    if ext_lower != '.webp' and os.path.isfile(fp_webp) and os.path.getsize(fp_webp):
                        delete(fp)
                        lgr.info(f'- {fp}')
                        continue
                    if ext_lower == '.thumb':
                        delete(fp)
                        lgr.info(f'- {fp}')
                        continue
            if cbz:
                if os.path.isdir(s):
                    lgr.info('# zip folder into cbz file')
                    dirs_with_image = []
                    for dp, sub_dirs, files in os.walk(s):
                        for f in files:
                            if re.match(r'.+\.(webp|jpg|jpeg|png)', f):
                                dirs_with_image.append(dp)
                                break
                    for dp in dirs_with_image:
                        cbz_fp = dp + '.cbz'
                        try:
                            fstk.make_zipfile_from_dir(cbz_fp, dp)
                        except NotADirectoryError:
                            lgr.info(f'! {dp}')
                        lgr.info(f'+ {cbz_fp} <- {dp}')
                        try:
                            delete(dp)
                        except (OSError, WindowsError):
                            sleep(1)
                            delete(dp)
                        lgr.info(f'- {dp}')
    finally:
        t = time.time() - t0
        n = cnt.n
        if verbose:
            cpr.ll()
        if n:
            lgr.info(f'{n} images in {naturaldelta(t)}, {naturaldelta(t / n)} per image')
        else:
            lgr.info(f'# no image file converted')


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
