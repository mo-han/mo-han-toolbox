#!/usr/bin/env python3
import shlex

from mylib.ex.console_app import *

if os.name != 'nt':
    raise NotImplementedError('launch new console window')


conf_path = fstk.make_path('%gallery-dl.conf%', env_var=True)
base_dir = fstk.make_path('%gallery-dl.base-directory%', env_var=True).strip('"')


class GLDLCLIArgs(CLIArgumentsList):
    merge_option_nargs = False


def new_gallery_dl_cmd(*args, **kwargs):
    cmd = GLDLCLIArgs('gallery-dl', R=10, c=conf_path,
                      o=f'base-directory={base_dir}', )
    return cmd


def get_cookies_path(middle_name):
    return fstk.make_path('%cookies.dir%', f'cookies.{middle_name}.txt', env_var=True)


def per_site(args: T.List[str]):
    first = args.pop(0)

    if first.startswith('/users/') or first.startswith('/artworks/'):
        url = 'https://www.pixiv.net' + first
    elif first == 'fanbox':
        url = f'https://{args.pop(0)}.fanbox.cc'
    elif first == 'twitter':
        url = f'https://twitter.com/{args.pop(0).lstrip("@")}/media'
    elif first == 'danbooru':
        url = f'https://danbooru.donmai.us/posts?tags={args.pop(0)}'
    elif first == 'gelbooru':
        url = f'https://gelbooru.com/index.php?page=post&s=list&tags={args.pop(0)}'
    elif first == 'sankaku':
        url = f'https://chan.sankakucomplex.com/?tags={args.pop(0)}'
    elif first == 'idol':
        url = f'https://idol.sankakucomplex.com/?tags={args.pop(0)}'
    else:
        url = first

    if 'pixiv.net' in url:
        args = [*GLDLCLIArgs(ugoira_conv=True,
                             o=['cookies-update=true',
                                'filename="pixiv.{id}_p{num}.{date:%Y-%m-%d}.{title}.{extension}"',
                                'directory=["[{user[name]}] {category} {user[id]}"]']),
                *args, url]
    elif 'fanbox.cc' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('fanbox'),
                             o=['cookies-update=true', 'videos=true',
                                'filename="{category}.{creatorId}.{id}_p{num}.{date!S:.10}.{filename}.{extension}"',
                                'directory=["[{user[name]}] pixiv {user[userId]} {category} {creatorId}"]']),
                *args, url]
    elif 'twitter.com' in url:
        args = [*GLDLCLIArgs(o=['filename="twitter.{tweet_id}_p{num}.{date:%Y-%m-%d}.{filename}.{extension}"',
                                'directory=["[{author[nick]}] {category} @{author[name]}"]', 'videos=true',
                                'retweets=false', 'content=true']),
                *args, url]
    elif 'danbooru.donmai.us' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('danbooru'),
                             o=['cookies-update=true', 'videos=true',
                                'filename="danbooru.{id}.{created_at:.10}.{md5}.'
                                '{tag_string_character:L64/(various)/}.{extension}"', 'videos=true',
                                'directory=["{category} {search_tags}"]', ]),
                *args, url]
    elif 'gelbooru.com' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('gelbooru'),
                             o=['cookies-update=true', 'videos=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{date!S:.10}.{md5}.{extension}"']),
                *args, url]
    elif 'sankakucomplex.com' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                             o=['cookies-update=true', 'videos=true',
                                'directory=["{category} {search_tags}"]',
                                'filename="{category}.{id}.{date!S:.10}.{md5}.{extension}"']),
                *args, url]
    else:
        raise NotImplementedError(url)

    return args


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
            os.system(f'start /min {__file__} {line}')
        except KeyboardInterrupt:
            sys.exit(2)


def main():
    args = sys.argv[1:]
    ostk.set_console_title(f'{path_basename(__file__)} - {args}')
    if not args:
        loop()
    else:
        cmd = new_gallery_dl_cmd() + per_site(args)
        try:
            p = subprocess.Popen(cmd)
            print(p.args)
            if p.wait():
                os.system('pause')
        except KeyboardInterrupt:
            sys.exit(2)


if __name__ == '__main__':
    main()
