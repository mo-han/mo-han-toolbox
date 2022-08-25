#!/usr/bin/env python3
import webbrowser

from mylib.ext.console_app import *

# if os.name != 'nt':
#     raise NotImplementedError('launch new console window')

env_var = os.environ
conf_path = fstk.make_path(env_var['gallery_dl_conf']).strip('"')
base_dir = fstk.make_path(env_var['gallery_dl_base_directory']).strip('"')
pause_on_error = os.environ.get('PAUSEONERROR', 'yes').lower() in {'yes', 'true', '1'}


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


def make_options_list(options_dict: dict):
    r = []
    for k, v in options_dict.items():
        if isinstance(v, str):
            r.append(f'{k}={v}')
        elif isinstance(v, T.Iterable):
            il = []
            for i in v:
                if isinstance(i, str):
                    il.append(f'"{i}"')
            r.append(f'{k}=[{", ".join(il)}]')
    return r


def new_gallery_dl_cmd(*args, **kwargs):
    cmd = GLDLCLIArgs('gallery-dl', R=-1, c=conf_path,
                      o=f'base-directory={base_dir}', )
    return cmd


def get_cookies_path(middle_name):
    return fstk.make_path(env_var['cookies_dir'], f'cookies.{middle_name}.txt')


class MultiList(list):
    pass


def per_site(site_args: T.List[str]):
    url = args2url(site_args)

    if 'pixiv.net' in url:
        args = [*GLDLCLIArgs(ugoira_conv=True,
                             o=['cookies-update=true',
                                'filename="{category} {date:%Y-%m-%d} {id}_p{num} {title} @{user[name]}.{extension}"',
                                'directory=["{user[name]} {category} {user[id]}"]']),
                *site_args, url]
    elif 'fanbox.cc' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('fanbox'),
                             o=['cookies-update=true', 'videos=true',
                                'filename="{category} {date!S:.10} {id}_p{num} {filename} @{creatorId}.{extension}"',
                                'directory=["{user[name]} {category} {user[userId]} {creatorId}"]']),
                *site_args, url]
    elif 'twitter.com' in url:
        args = [*GLDLCLIArgs(o=['videos=true', 'retweets=false', 'content=true',
                                'filename="{category} {date:%Y-%m-%d} {tweet_id}_p{num} {filename} '
                                '{content!S:.48} @{author[name]}.{extension}"',
                                'directory=["{author[nick]} {category} @{author[name]}"]']),
                *site_args, url]
    elif 'danbooru.donmai.us' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('danbooru'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{search_tags} {category}"]',
                                'filename="{category} {created_at:.10} {id} {md5} '
                                '{tag_string_character!S:L80/(various)/} @{tag_string_artist!S:L80/(various)/}.'
                                '{extension}"', ]),
                *site_args, url]
    elif 'gelbooru.com' in url:
        args = [*GLDLCLIArgs(
            cookies=get_cookies_path('gelbooru'),
            o=['cookies-update=true', 'videos=true', 'tags=true',
               'directory=["{search_tags} {category}"]',
               'filename="{category} {date!S:.10} {id} {md5} '
               '{tags_character!S:L80/___/} '
               '©{tags_copyright!S:L40/___/} '
               '@{tags_artist!S:L40/___/}'
               '.{extension}"', ]
        ),
                *site_args, url]
    elif 'realbooru.com' in url:
        args = [*GLDLCLIArgs(
            # cookies=get_cookies_path('realbooru'),
            o=[
                'cookies-update=true', 'videos=true', 'tags=true',
                'directory=["{search_tags} {category}"]',
                'filename="{category} {date!S:.10} {id} {md5} '
                '{search_tags!S:.80}.{extension}"'
            ]
        ),
                *site_args, url]
    elif 'rule34.xxx' in url:
        args = [*GLDLCLIArgs(
            o=['cookies-update=true', 'videos=true', 'tags=true',
               'directory=["{search_tags} {category}"]',
               'filename="{category} {date!S:.10} {id} {md5} '
               '{tags_character!S:L80/(various)/} @{tags_artist!S:L80/(various)/}.{extension}"', ]
        ),
                *site_args, url]
    elif 'chan.sankakucomplex.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5} '
            '{tag_string_character!S:L80/___/} '
            '©{tag_string_copyright!S:L40/___/} '
            '@{tag_string_artist!S:L40/___/}'
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                         o=[*options, 'directory=["{search_tags} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = int(pq_arg[2:])
                tags_s = url.split('/?tags=', maxsplit=1)[-1].strip()
                gldl_args = GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                                        o=[*options, f'directory=["{tags_s} {{category}} {pq_arg}"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', f'-{num}', url + ' order:popular'],
                    [*gldl_args, *site_args, '--range', f'-{num}', url + ' order:quality'],
                ])
    elif 'idol.sankakucomplex.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {created_at!S:.10} {id} {md5} '
            '©{tags_photo_set!S:L80/___/} '
            '@{tags_idol!S:L80/___/}.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(cookies=get_cookies_path('sankaku.idol'),
                         o=[*options, 'directory=["{search_tags} {category}"]']),
            *site_args, url
        ]
    elif 'newgrounds.com' in url:
        args = [*GLDLCLIArgs(o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{user} {category}"]',
                                'filename="{category} {date!S:.10} {index} '
                                '{title} @{artist!S:L80/(various)/}.{extension}"', ]),
                *site_args, url]
    elif 'kemono.party' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('kemonoparty'),
                             o=['cookies-update=true', 'videos=true', 'tags=true', 'metadata=true',
                                'directory=["{username} {category} {service} {user}"]',
                                'filename="{category} {service} {date!S:.10} {id}_p{num} {filename} '
                                '{title} @{username}.{extension}"', ]),
                *site_args, url]
    elif 'nhentai' in url:
        args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{title} [{category} {gallery_id}]'],
            filename='{filename}.{extension}'
        ))), *site_args, url]
    elif 'hentai-foundry' in url:
        args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{artist} {category}'],
            filename='{category} {date!S:.10} {index} {title} @{artist}.{extension}'
        ))), *site_args, url]
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
    elif first == 'realbooru':
        url = f'https://realbooru.com/index.php?page=post&s=list&tags={pop_tag_from_args(args)}'
    elif first == 'sankaku':
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://chan.sankakucomplex.com/post/show/{x}'
        else:
            url = f'https://chan.sankakucomplex.com/?tags={x}'
    elif first in ('idol', 'idolcomplex'):
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://idol.sankakucomplex.com/post/show/{x}'
        else:
            url = f'https://idol.sankakucomplex.com/?tags={x}'
    elif first in ('ng', 'newgrounds'):
        url = f'https://{pop_tag_from_args(args)}.newgrounds.com/art'
    elif first in ('kemono', 'kemonoparty', 'kemono.party'):
        url = f'https://kemono.party/{pop_tag_from_args(args)}'
    else:
        url = first
    if url.startswith('https://twitter.com/') and not url.endswith('/media'):
        url += '/media'
    url = url.replace('chan.sankakucomplex.com/cn/', 'chan.sankakucomplex.com/')
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
        site_args = per_site(args)
        cmd_l = []
        if isinstance(site_args, MultiList):
            for i in site_args:
                cmd_l.append(new_gallery_dl_cmd() + i)
        else:
            cmd_l.append(new_gallery_dl_cmd() + site_args)
        for cmd in cmd_l:
            try:
                p = subprocess.Popen(cmd)
                print(p.args)
                if p.wait() and pause_on_error:
                    console_pause()
            except KeyboardInterrupt:
                sys.exit(2)


if __name__ == '__main__':
    main()
