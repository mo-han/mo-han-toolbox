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
    cmd = GLDLCLIArgs('gallery-dl', R=20, c=conf_path,
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
                                'filename="{category} {date:%Y-%m-%d} {id} '
                                '{title} @{user[name]} {filename}.{extension}"',
                                'directory=["{user[name]} {category} {user[id]}"]']),
                *site_args, url]
    elif 'fanbox.cc' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('fanbox'),
                             o=['cookies-update=true', 'videos=true',
                                'filename="{category} {date!S:.10} {id} '
                                '{title} @{creatorId} {filename}.{extension}"',
                                'directory=["{user[name]} {category} {user[userId]} {creatorId}"]']),
                *site_args, url]
    elif 'twitter.com' in url:
        args = [*GLDLCLIArgs(o=['videos=true', 'retweets=false', 'content=true',
                                'filename="{category} {date:%Y-%m-%d} {tweet_id} '
                                '{content!S:.48} @{author[name]} p{num} {filename}.{extension}"',
                                'directory=["{author[nick]} {category} @{author[name]}"]']),
                *site_args, url]
    elif 'danbooru.donmai.us' in url:
        args = [*GLDLCLIArgs(cookies=get_cookies_path('danbooru'),
                             o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{search_tags!S} {category}"]',
                                'filename="{category} {created_at:.10} {id} {md5} '
                                '{tag_string_character!S:L80/___/} '
                                '@{tag_string_artist!S:L80/___/} '
                                '.{extension}"', ]),
                *site_args, url]
    elif 'gelbooru.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5} '
            '{tags_character!S:L80/___/} '
            '${tags_copyright!S:L40/___/} '
            '@{tags_artist!S:L80/___/} '
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = pq_arg[2:]
                if '-' not in num:
                    num = f'1-{num}'
                tags_s = url.split('&tags=', maxsplit=1)[-1].strip()
                # gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} {pq_arg}"]'])
                gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', num, url + ' sort:score'],
                ])
    elif 'aibooru.online' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5} '
            '{tag_string_character!S:L80/___/} '
            '${tag_string_copyright!S:L40/___/} '
            '@{tag_string_artist!S:L40/___/} {tag_string_model!S}'
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(cookies=get_cookies_path('aibooru'),
                         o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = pq_arg[2:]
                if '-' not in num:
                    num = f'1-{num}'
                tags_s = url.split('?tags=', maxsplit=1)[-1].strip()
                print(url, tags_s)
                gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', num, url + ' order:rank'],
                    [*gldl_args, *site_args, '--range', num, url + ' order:views'],
                    [*gldl_args, *site_args, '--range', num, url + ' order:score'],
                    [*gldl_args, *site_args, '--range', num, url + ' order:favcount'],
                ])

    elif 'realbooru.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5} '
            '${tags_copyright!S:L40/___/} '
            '@{tags_model!S:L80/___/} '
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = pq_arg[2:]
                if '-' not in num:
                    num = f'1-{num}'
                tags_s = url.split('&tags=', maxsplit=1)[-1].strip()
                gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', num, url + ' sort:score'],
                ])

    elif 'rule34.xxx' in url:
        args = [*GLDLCLIArgs(
            o=['cookies-update=true', 'videos=true', 'tags=true',
               'directory=["{search_tags!S} {category}"]',
               'filename="{category} {date!S:.10} {id} {md5} '
               '{tags_character!S:L80/___/} @{tags_artist!S:L80/___/} .{extension}"', ]
        ),
                *site_args, url]
    elif 'chan.sankakucomplex.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5} '
            '{tag_string_character!S:L80/___/} '
            '${tag_string_copyright!S:L40/___/} '
            '@{tag_string_artist!S:L40/___/} '
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                         o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = pq_arg[2:]
                if '-' not in num:
                    num = f'1-{num}'
                tags_s = url.split('/?tags=', maxsplit=1)[-1].strip()
                gldl_args = GLDLCLIArgs(cookies=get_cookies_path('sankaku'),
                                        o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', num, url + ' order:popular'],
                    [*gldl_args, *site_args, '--range', num, url + ' order:quality'],
                ])
    elif 'idol.sankakucomplex.com' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {created_at!S:.10} {id} {md5} '
            '{tags_photo_set!S:L40/___/} '
            '${tags_copyright!S:L40/___/} '
            '@{tags_idol!S:L80/___/} '
            '.{extension}"',
        ]
        args = [
            *GLDLCLIArgs(cookies=get_cookies_path('sankaku.idol'),
                         o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *site_args, url
        ]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = pq_arg[2:]
                if '-' not in num:
                    num = f'1-{num}'
                tags_s = url.split('/?tags=', maxsplit=1)[-1].strip()
                gldl_args = GLDLCLIArgs(cookies=get_cookies_path('sankaku.idol'),
                                        o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                # o=[*options, f'directory=["{tags_s} {{category}} {pq_arg}"]'])
                args = MultiList([
                    [*gldl_args, *site_args, '--range', num, url + ' order:popular'],
                    [*gldl_args, *site_args, '--range', num, url + ' order:quality'],
                ])
    elif 'reddit.com' in url:
        gldl_args = GLDLCLIArgs(o='parent-skip=true')
        args = [*gldl_args, *site_args, url]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = int(pq_arg[2:])
                sort_types = ['hot', 'top/?t=all', 'gilded', 'best']
                if any(s in url for s in sort_types):
                    args = [*gldl_args, *site_args, '--range', {num}, url]
                else:
                    args = MultiList([
                        [
                            *gldl_args, *site_args,
                            '--range', f'-{num // 10 if sort == "hot" else num}',
                            '--chapter-range', f'-{num // 10 if sort == "hot" else num}',
                            url.rstrip('/') + f'/{sort}'
                        ] for sort in sort_types
                    ])
    elif 'redgifs.com' in url:
        gldl_args = GLDLCLIArgs()
        args = [*gldl_args, *site_args, url]
        if site_args:
            pq_arg, *site_args = site_args
            if pq_arg.startswith('pq'):
                num = int(pq_arg[2:])
                args = MultiList([
                    [*gldl_args, *site_args, f'--range', f'-{num}', url + '?order=trending'],
                    [*gldl_args, *site_args, f'--range', f'-{num}', url + '?order=best'],
                ])
    elif 'luscious.net' in url:
        args = [
            *GLDLCLIArgs(o=[
                'videos=true', 'tags=true',
                'directory=["{album[title]} {category} {subcategory} {album[id]} {album[description]:.100}"]',
                'filename="{category} {subcategory} {album[id]} {album[title]} {id} {title}.{extension}"',
            ]),
            *site_args, url
        ]
    elif 'newgrounds.com' in url:
        args = [*GLDLCLIArgs(o=['cookies-update=true', 'videos=true', 'tags=true',
                                'directory=["{user} {category}"]',
                                'filename="{category} {date!S:.10} {index} '
                                '{title} @{artist!S:L80/___/} .{extension}"', ]),
                *site_args, url]
    elif 'kemono.party' in url or 'coomer.party' in url:
        args = [
            *GLDLCLIArgs(
                o=[
                    'cookies-update=true', 'videos=true', 'tags=true', 'metadata=true',
                    'directory=["{username} {category} {service} {user}"]',
                    'filename="{category} {service} {date!S:.10} {id} '
                    '{title:.60} @{username} p{num} {filename:.40}.{extension}"',
                ],
                filter="extension not in ('psd', 'clip')",
            ),
            *site_args, url
        ]
    elif 'nhentai' in url:
        args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{category}', '{title} {category} {gallery_id}'],
            filename='{filename}.{extension}'
        ))), *site_args, url]
    elif 'hentai-foundry' in url:
        args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{artist} {category}'],
            filename='{category} {date!S:.10} {index} {title} @{artist}.{extension}'
        ))), *site_args, url]
    else:
        args = [*GLDLCLIArgs(), *site_args, url]

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
    elif first in ('gelbooru', 'gel'):
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://gelbooru.com/index.php?page=post&s=view&id={x}'
        else:
            url = f'https://gelbooru.com/index.php?page=post&s=list&tags={x}'
    elif first in ('realbooru', 'real'):
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://realbooru.com/index.php?page=post&s=view&id={x}'
        else:
            url = f'https://realbooru.com/index.php?page=post&s=list&tags={x}'
    elif first in ('sankaku', 'chan'):
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
    elif first in ('coomer', 'coomerparty', 'coomer.party'):
        url = f'https://coomer.party/{pop_tag_from_args(args)}'
    elif first in ('luscious', 'lus'):
        x = pop_tag_from_args(args)
        if re.match(r'\d+ \d+', x):
            a, b = x.split()
            url = f'https://www.luscious.net/pictures/album/{a}/id/{b}'
        else:
            url = f'https://www.luscious.net/albums/{x}'
    elif first in ('reddit',):
        url = f'https://www.reddit.com/{pop_tag_from_args(args)}'
    elif first in ('redgifs',):
        url = f'https://www.redgifs.com/gifs/{pop_tag_from_args(args)}'
    elif first in ('ai', 'aibooru',):
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://aibooru.online/posts/{x}'
        else:
            url = f'https://aibooru.online/posts?tags={x}'
    else:
        url = first
    if url.startswith('https://twitter.com/') and '/status/' not in url and not url.endswith('/media'):
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
