#!/usr/bin/env python3
from mylib.ex.console_app import *
from mylib.sites import ehentai

apr = ArgumentParserRigger()
an = apr.an
cp = ConsolePrinter()
an.src = an.v = an.verbose = an.D = an.dry_run = an.address = an.c = an.cookies = an.p = an.proxy = ''


def main():
    apr.parse()
    apr.run()


@apr.sub(apr.rnu(), aliases=['mvfav'])
@apr.arg(an.cookies)
@apr.arg('from', choices=[str(i) for i in range(10)], help='src fav slot', metavar='from')
@apr.arg('to', choices=[str(i) for i in range(10)], help='dst fav slot', metavar='to')
@apr.opt(an.p, an.proxy)
@apr.true(an.v, an.verbose)
@apr.map(an.cookies, 'from', 'to', an.proxy, an.verbose)
def migrate_favorites(cookies, from_favorite, to_favorite, proxy, verbose):
    """move all favorites in one slot to another"""
    from mylib.ex.splinter import Browser, http_headers, BrowserWrapper, make_proxy_settings

    if from_favorite == to_favorite:
        raise ValueError('from same as to')
    url = f'https://exhentai.org/favorites.php?favcat={from_favorite}'
    dst = f'fav{to_favorite}'
    choose_all = 'alltoggle'
    action = 'ddact'
    apply = 'apply'

    with BrowserWrapper(Browser(profile_preferences={
        **make_proxy_settings(proxy),
        'permissions.default.image': 2
    }, headless=not verbose)) as w:
        w.visit(url)
        w.add_cookies(http_headers.get_cookies_dict_from(cookies))
        w.visit(url)
        while 1:
            while w.not_exist(id=choose_all, wait_time=0.2):
                sleep(0.2)
            if w.not_exist(css='.itg'):
                break
            w.find(id=choose_all).last.check()
            w.find(name=action).last.select(dst)
            w.find(name=apply).last.click()
        if verbose:
            input('press enter to exit')


def _sorted_path_of_hentai_at_home_downloaded_gallery(gallery_path, gallery_type=''):
    _unknown_ = '(unknown)'
    _various_ = '(various)'

    info = ehentai.parse_hentai_at_home_downloaded_gallery_info(gallery_path, gallery_type)
    if not info:
        return None
    title = info['title']
    sanitized_title = fstk.sanitize_xu240(title)
    artist = info['tags']['artist']
    group = info['tags']['group']
    root_dir, name, ext = split_path_dir_base_ext(gallery_path, dir_ext=False)

    creators = artist or group or []
    if len(creators) > 3:
        creators_s = _various_
    else:
        creators_s = ', '.join(creators) or _unknown_

    new_root = fstk.make_path(root_dir, creators_s)
    dst: str = join_path_dir_base_ext(new_root, f'{sanitized_title} {info["gid_resize"]}', ext)
    return dst


@apr.sub(apr.rename_underscore())
@apr.arg(an.src, nargs='*')
@apr.true(an.v, an.verbose)
@apr.true(an.D, apr.dst2opt(an.dry_run))
@apr.map(an.src, verbose=an.verbose, dry_run=an.dry_run)
def hath_sort(src: PathSourceType, *, verbose=False, dry_run=False):
    """rename and sort galleries downloaded via H@H (Hentai at Home)"""
    dirs, files = resolve_path_to_dirs_files(src)
    src_dst_l = []
    [src_dst_l.append((src, _sorted_path_of_hentai_at_home_downloaded_gallery(src, 'd'))) for src in dirs]
    [src_dst_l.append((src, _sorted_path_of_hentai_at_home_downloaded_gallery(src, 'f'))) for src in files]
    for src, dst in src_dst_l:
        if not dst and verbose:
            print(f'# {src}')
            continue
        try:
            if not dry_run:
                fstk.move_as(src, dst)
            if verbose:
                print(f'* {dst} <- {src}')
        except Exception as e:
            if verbose:
                print(f'! {src}: {repr(e)}')


@apr.sub(apr.rename_underscore(), aliases=['rc'])
@apr.arg(an.address, help='remote address for adb connect')
@apr.map(an.address)
def remote_control(remote_address: str):
    """remote control ehviewer app via adb"""
    from mylib.ex.pure_python_adb import ADBClient
    from pynput.keyboard import Listener, KeyCode, Key

    client = ADBClient()
    if not client.connect(remote_address):
        print(f'! cannot connect to {remote_address}')
        sys.exit(1)
    devices = [d for d in client.devices() if d.serial == remote_address]
    if devices:
        device = devices[0]
    else:
        device = [d for d in client.devices() if d.serial.startswith(remote_address)][0]
    width, height = map(int,
                        re.search(r'cur=(\d+)x(\d+)', device.shell('dumpsys window displays')).groups())
    center_x, center_y = width / 2, height / 2
    center_y_lower = center_y + 130

    def on_press(key: Key):
        key2input = {
            KeyCode(char='s'): [(device.input_swipe, (center_x, center_y, center_x, center_y, 0.6)),
                                (device.input_tap, (center_x, center_y_lower))],
            KeyCode(char='j'): [(device.input_roll, (0, -1))],
            KeyCode(char='k'): [(device.input_roll, (0, 1))],
            KeyCode(char='h'): [(device.input_roll, (0, -10))],
            KeyCode(char='l'): [(device.input_roll, (0, 10))],
            KeyCode(char='n'): [(device.input_roll, (0, -100))],
            KeyCode(char='m'): [(device.input_roll, (0, 100))],
            Key.esc: [(sys.exit, (2,))],
        }
        call_list = key2input.get(key, [])
        for func, args in call_list:
            cp.il(f'{func.__name__}{args}')
            func(*args)

    with Listener(on_press=on_press) as lr:
        print('# launched')
        cp.ll()
        lr.join()


if __name__ == '__main__':
    main()
