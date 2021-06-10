#!/usr/bin/env python3
import webbrowser

from mylib.ex.console_app import *

if os.name != 'nt':
    raise NotImplementedError('launch new console window')

conf_path = fstk.make_path('%gallery-dl.conf%', env_var=True)
base_dir = fstk.make_path('%gallery-dl.base-directory%', env_var=True).strip('"')


def _console_pause_nt():
    os.system('pause')


def _console_pause():
    os.system('read -p "press any key to continue . . ." -srn1')


def _console_new_run_nt(cmd):
    os.system(f'start /min {cmd}')


def _console_new_run(cmd):
    os.system(f'xterm -iconic -e {cmd}')


if os.name == 'nt':
    console_new_run = _console_new_run_nt
    console_pause = _console_pause_nt
else:
    console_new_run = _console_new_run
    console_pause = _console_pause


class GLDLCLIArgs(CLIArgumentsList):
    merge_option_nargs = False


def new_gallery_dl_cmd(*args, **kwargs):
    cmd = GLDLCLIArgs('gallery-dl', R=10, c=conf_path,
                      o=f'base-directory={base_dir}', )
    return cmd


def get_cookies_path(middle_name):
    return fstk.make_path('%cookies.dir%', f'cookies.{middle_name}.txt', env_var=True)


def per_site(args: T.List[str]):
    url = args2url(args)

    if 'pixiv.net' in url:
        args = [*GLDLCLIArgs(ugoira_conv=True,
                             o=['cookies-update=true',
                                'filename="{category}.{id}_p{num}.{date:%Y-%m-%d}.{title}.{extension}"',
                                'directory=["[{user[name]}] {category} {user[id]}"]']),
                *args, url]
    elif 'fanbox.cc' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('fanbox'),
                             o=['cookies-update=true', 'videos=true',
                                'filename="{category}.{id}_p{num}.{date!S:.10}.{filename}.@{creatorId}.{extension}"',
                                'directory=["[{user[name]}] pixiv {user[userId]} {category} {creatorId}"]']),
                *args, url]
    elif 'twitter.com' in url:
        args = [*GLDLCLIArgs(o=['videos=true', 'retweets=false', 'content=true',
                                'filename="twitter.{tweet_id}_p{num}.{date:%Y-%m-%d}.{filename}.{extension}"',
                                'directory=["[{author[nick]}] {category} @{author[name]}"]']),
                *args, url]
    elif 'danbooru.donmai.us' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('danbooru'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{created_at:.10}.{md5}.'
                                '{tag_string_character!S:L80/(various)/}.{tag_string_artist!S:L80/(various)/}.'
                                '{extension}"', ]),
                *args, url]
    elif 'gelbooru.com' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('gelbooru'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{date!S:.10}.{md5}.'
                                '{tags_character!S:L80/(various)/}.{tags_artist!S:L80/(various)/}.{extension}"', ]),
                *args, url]
    elif 'chan.sankakucomplex.com' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{date!S:.10}.{md5}.'
                                '{tag_string_character!S:L80/(various)/}.{tag_string_artist!S:L80/(various)/}.'
                                '{extension}"', ]),
                *args, url]
    elif 'idol.sankakucomplex.com' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{date!S:.10}.{md5}.'
                                '{tags_idol!S:L80/(various)/}.{extension}"', ]),
                *args, url]
    elif 'newgrounds.com' in url:
        args = [*GLDLCLIArgs(o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["[{user}] {category}"]',
                                'filename="{category}.{index}.{date!S:.10}.'
                                '{title}.{artist!S:L80/(various)/}.{extension}"', ]),
                *args, url]
    else:
        raise NotImplementedError(url)

    return args


def pop_tag_from_args(args):
    return fstk.sanitize_xu(re.sub(r'[\[\]]', '', args.pop(0)), reverse=True,
                            unescape_html=False, decode_url=False, unify_white_space=False)


def args2url(args):
    first = args.pop(0)
    if first.startswith('/users/') or first.startswith('/artworks/'):
        url = 'https://www.pixiv.net' + first
    elif first == 'fanbox':
        url = f'https://{args.pop(0)}.fanbox.cc'
    elif first == 'twitter':
        url = f'https://twitter.com/{args.pop(0).lstrip("@")}/media'
    elif first == 'danbooru':
        url = f'https://danbooru.donmai.us/posts?tags={pop_tag_from_args(args)}'
    elif first == 'gelbooru':
        url = f'https://gelbooru.com/index.php?page=post&s=list&tags={pop_tag_from_args(args)}'
    elif first == 'sankaku':
        url = f'https://chan.sankakucomplex.com/?tags={pop_tag_from_args(args)}'
    elif first == 'idol':
        url = f'https://idol.sankakucomplex.com/?tags={pop_tag_from_args(args)}'
    elif first in ('ng', 'newgrounds'):
        url = f'https://{pop_tag_from_args(args)}.newgrounds.com/art'
    else:
        url = first
    if url.startswith('https://twitter.com/') and not url.endswith('/media'):
        url += '/media'
    return url


def loop():
    cp = ConsolePrinter()
    cp.ll()
    while 1:
        try:
            line = input()
            if not line.strip():
                continue
            if line == 'q':
                sys.exit(0)
            console_new_run(f'{__file__} {line}')
        except KeyboardInterrupt:
            sys.exit(2)


def main():
    args = sys.argv[1:]
    ostk.set_console_title(f'{path_basename(__file__)} - {args}')
    if not args:
        loop()
    else:
        if args[0] == 'o':
            args.pop(0)
            url = args2url(args)
            return webbrowser.open_new_tab(url)
        cmd = new_gallery_dl_cmd() + per_site(args)
        try:
            p = subprocess.Popen(cmd)
            print(p.args)
            if p.wait():
                console_pause()
        except KeyboardInterrupt:
            sys.exit(2)


if __name__ == '__main__':
    main()
