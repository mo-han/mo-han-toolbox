#!/usr/bin/env python3
import os.path
import re
import string
import webbrowser

import requests

from mylib.ext.console_app import *

# if os.name != 'nt':
#     raise NotImplementedError('launch new console window')

STRING_NOT_WANT = '.not_want'

env_var = os.environ
base_dir = fstk.make_path(env_var['gallery_dl_base_directory']).strip('"')
pause_on_error = os.environ.get('PAUSEONERROR', 'yes').lower() in {'yes', 'true', '1'}

runtime_data = {}


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
    cmd = GLDLCLIArgs('gallery-dl', R=20,
                      o=f'base-directory={base_dir}', )
    return cmd


def get_cookies_path(middle_name):
    return fstk.make_path(env_var['cookies_dir'], f'cookies.{middle_name}.txt')


class MultiList(list):
    pass


def per_site(args: T.List[str]):
    url = args2url(args)
    # todo#mark pixiv
    if 'pixiv.net' in url:
        gldl_args = GLDLCLIArgs(
            ugoira_conv=True,
            o=[
                'cookies-update=true',
                'filename="{category} {date:%Y-%m-%d} {id} {title} {page_count}p '
                '@{user[name]} p{num}.{extension}"',
                'directory=["{user[name]} {category} {user[id]}"]'
            ],
        )
        if args:
            arg0 = args[0]
            if os.path.isfile(arg0):
                gldl_args.extend(['-i', *args])
            elif arg0 == 'bg':
                more_args = ['-o', 'extractor.pixiv.include=["background","avatar"]']
                if '/users/' in url:
                    gldl_args.extend([*args[1:], *more_args, url])
                else:
                    gldl_args.extend([*args[2:], *more_args, f'https://www.pixiv.net/users/{args[1]}'])
            elif arg0 in ('u', 'user'):
                gldl_args.extend([*args[2:], f'https://www.pixiv.net/users/{args[1]}'])
            elif arg0 in ('a', 'art', 'artwork'):
                gldl_args.extend([*args[2:], f'https://www.pixiv.net/artworks/{args[1]}'])
            else:
                gldl_args.extend([*args, url])
        else:
            gldl_args.append(url)
    elif 'fanbox.cc' in url:
        gldl_args = [*GLDLCLIArgs(
            o=['cookies-update=true', 'videos=true',
               'filename="{category} {date!S:.10} {id} {title} {page_count}p '
               '@{creatorId} p{num}.{extension}"',
               'directory=["{user[name]} {category} {user[userId]} {creatorId}"]']),
                     *args, url]
    elif 'twitter.com' in url or 'https://x.com/' in url:
        gldl_args = [*GLDLCLIArgs(o=['videos=true', 'retweets=false', 'content=true',
                                     'filename="{category} {date!S:.10} {tweet_id} {content!S:.48} {count}p '
                                     '@{author[name]} p{num}.{extension}"',
                                     'directory=["{author[nick]} {category} @{author[name]}"]']),
                     *args, url]
    elif 'danbooru.donmai.us' in url:
        gldl_args = [*GLDLCLIArgs(user_agent='auto',
                                  o=['cookies-update=true', 'videos=true', 'tags=true',
                                     'directory=["{search_tags!S} {category}"]',
                                     'filename="{category} {created_at:.10} {id} {md5}'
                                     ' {tag_string_character!S:L80/___/}'
                                     ' $ {tag_string_copyright!S:L40/___/}'
                                     ' @ {tag_string_artist!S:L80/___/}'
                                     ' .{extension}"', ]),
                     *args, url]
    elif 'gelbooru.com' in url:
        # todo#mark gelbooru
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tags_character!S:L80/___/}'
            ' $ {tags_copyright!S:L40/___/}'
            ' @ {tags_artist!S:L80/___/}'
            ' .{extension}"',
        ]
        gldl_args = [
            *GLDLCLIArgs(o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *args, url
        ]
        if args:
            pq_arg, *args = args
            if pq_arg.startswith('pq'):
                pq_value = pq_arg[2:]
                if '-' not in pq_value:
                    pq_value = f'1-{pq_value}'
                tags_s = url.split('&tags=', maxsplit=1)[-1].strip()
                # gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} {pq_arg}"]'])
                gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                gldl_args = MultiList([
                    [*gldl_args, *args, '--range', pq_value, url + ' sort:score'],
                ])
    elif 'aibooru.online' in url:
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tag_string_character!S:L80/___/} '
            ' $ {tag_string_copyright!S:L40/___/} '
            ' @ {tag_string_artist!S:L80/___/} {tag_string_model!S}'
            ' .{extension}"',
        ]
        gldl_args = [
            *GLDLCLIArgs(o=[*options, 'directory=["{search_tags!S} {category}"]']),
            *args, url
        ]
        if args:
            pq_arg, *args = args
            if pq_arg.startswith('pq'):
                pq_value = pq_arg[2:]
                if '-' not in pq_value:
                    pq_value = f'1-{pq_value}'
                tags_s = url.split('?tags=', maxsplit=1)[-1].strip()
                print(url, tags_s)
                gldl_args = GLDLCLIArgs(o=[*options, f'directory=["{tags_s} {{category}} pq"]'])
                gldl_args = MultiList([
                    [*gldl_args, *args, '--range', pq_value, url + ' order:rank'],
                    [*gldl_args, *args, '--range', pq_value, url + ' order:views'],
                    [*gldl_args, *args, '--range', pq_value, url + ' order:score'],
                    [*gldl_args, *args, '--range', pq_value, url + ' order:favcount'],
                ])

    elif 'rule34.xxx' in url:
        gldl_args = [*GLDLCLIArgs(
            o=['cookies-update=true', 'videos=true', 'tags=true',
               'directory=["{search_tags!S} {category}"]',
               'filename="{category} {date!S:.10} {id} {md5} '
               '{tags_character!S:L80/___/} @{tags_artist!S:L80/___/} .{extension}"', ]
        ),
                     *args, url]

    elif 'realbooru.com' in url:
        site_name = 'realbooru'
        site_host = 'realbooru.com'
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5}'
            ' $ {tags_copyright!S:L64/___/}'
            ' @ {tags_model!S:L64/___/}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': ['sort:score', ],
            'tag_path_prefix': '/index.php?page=post&s=list&tags=',
            'post_path_prefix': '/index.php?page=post&s=view&id=',
        }

        gldl_args = sankaku_site_args_func(options, args, site_host, site_name, url, site_settings)

    elif 'chan.sankakucomplex.com' in url:
        # todo#mark sankaku
        site_name = 'sankaku'
        site_host = 'chan.sankakucomplex.com'
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tag_string_character!S:L80/___/}'
            ' $ {tag_string_copyright!S:L40/___/}'
            ' @ {tag_string_artist!S:L80/___/} '
            '.{extension}"',
        ]
        site_settings = {
            'sort_tag_list': ['order:popular', 'order:quality'],
            'tag_path_prefix': '/?tags=',
            'post_path_prefix': '/posts/',
        }

        gldl_args = sankaku_site_args_func(options, args, site_host, site_name, url, site_settings)

    elif 'idol.sankakucomplex.com' in url:
        site_name = 'idolcomplex'
        site_host = 'idol.sankakucomplex.com'
        options = [
            'cookies-update=true', 'videos=true', 'tags=true',
            'filename="{category} {created_at!S:.10} {id} {md5}'
            ' {tags_photo_set!S:L80/___/}'
            ' $ {tags_copyright!S:L40/___/} {tags_studio!S:L40/___/}'
            ' @ {tags_idol!S:L80/___/}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': ['order:popular', 'order:quality'],
            'tag_path_prefix': '/?tags=',
            'post_path_prefix': '/posts/',
        }

        gldl_args = sankaku_site_args_func(options, args, site_host, site_name, url, site_settings)

    elif 'reddit.com' in url:
        gldl_args = [*GLDLCLIArgs(), *args, url]
        if args:
            pq_arg, *args = args
            if pq_arg.startswith('pq'):
                pq_value = pq_arg[2:]
                if '-' not in pq_value:
                    pq_value = f'1-{pq_value}'
                sort_types = ['/hot', '/top/?t=all', '/gilded', '/best']
                if any(s in url for s in sort_types) or '/search?q=' in url or '/search/?q=' in url:
                    gldl_args = [*GLDLCLIArgs(), *args, '--range', pq_value, '--chapter-range',
                                 f"1-{pq_value.split('-')[-1]}", url]
                if '/search?q=' in url and 'sort=relevance' in url:
                    gldl_args = MultiList([
                        [*GLDLCLIArgs(), *args, '--range', pq_value, '--chapter-range',
                         f"1-{pq_value.split('-')[-1]}", u] for u in (url, url.replace('sort=relevance', 'sort=top'))
                    ])
                else:
                    gldl_args = MultiList([
                        [
                            *GLDLCLIArgs(), *args,
                            '--range', pq_value, '--chapter-range', f"1-{pq_value.split('-')[-1]}",
                            url.rstrip('/') + f'{sort}'
                        ] for sort in sort_types
                    ])
                print(gldl_args)
    elif 'redgifs.com' in url:
        gldl_args = [*GLDLCLIArgs(), *args, url]
        if args:
            pq_arg, *args = args
            if pq_arg.startswith('pq'):
                pq_value = int(pq_arg[2:])
                gldl_args = MultiList([
                    [*GLDLCLIArgs(), *args, f'--range', f'1-{pq_value}', url + '?order=trending'],
                    [*GLDLCLIArgs(), *args, f'--range', f'1-{pq_value}', url + '?order=best'],
                ])
    elif 'luscious.net' in url:
        gldl_args = [
            *GLDLCLIArgs(o=[
                'videos=true', 'tags=true',
                'directory=["{album[title]} {category} {subcategory} {album[id]} {album[description]:.100}"]',
                'filename="{category} {subcategory} {album[id]} {album[title]} {id} {title}.{extension}"',
            ]),
            *args, url
        ]
    elif 'newgrounds.com' in url:
        gldl_args = [*GLDLCLIArgs(o=['cookies-update=true', 'videos=true', 'tags=true',
                                     'directory=["{user} {category}"]',
                                     'filename="{category} {date!S:.10} {index} '
                                     '{title} @{artist!S:L80/___/} .{extension}"', ]),
                     *args, url]
    elif 'kemono.' in url or 'coomer.' in url:
        # todo#mark kemono
        gldl_args = [
            *GLDLCLIArgs(
                o=[
                    'cookies-update=true', 'videos=true', 'tags=true', 'metadata=true',
                    'directory=["{username} {category} {service} {user}"]',
                    'filename="{category} {service} {date!S:.10} {id} {title:.60} {count}p '
                    '@{username} p{num} {filename:.40}.{extension}"',
                ],
                filter="extension not in ('psd', 'clip')",
            ),
            *args, url
        ]
        if url in ('kemono.', 'commer.'):
            gldl_args.pop()
    elif 'nhentai' in url:
        gldl_args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{category}', '{title} {category} {gallery_id}'],
            filename='{filename}.{extension}'
        ))), *args, url]
    elif 'hentai-foundry' in url:
        gldl_args = [*GLDLCLIArgs(o=make_options_list(dict(
            directory=['{artist} {category}'],
            filename='{category} {date!S:.10} {index} {title} @{artist}.{extension}'
        ))), *args, url]
    else:
        gldl_args = [*GLDLCLIArgs(), *args, url]

    return gldl_args


def sankaku_site_args_func(options, site_args, site_host, site_name, url, site_settings):
    post_path_prefix = site_settings['post_path_prefix']
    tag_path_prefix = site_settings['tag_path_prefix']
    args = [
        *GLDLCLIArgs(
            o=[*options, 'directory=["{search_tags!S} {category}"]'],
        ),
        *site_args, url
    ]
    if site_args:
        tags_s = url.split(tag_path_prefix, maxsplit=1)[-1].strip()
        pq_arg, *site_args = site_args
        if pq_arg.startswith('pq'):
            pq_value = pq_arg[2:]
            if set(pq_value) <= set(string.digits):
                pq_value = f'1-{pq_value}'
            if set(pq_value) <= set(string.digits + '-'):
                head_args = GLDLCLIArgs(
                    o=[*options, f'directory=["{tags_s} {{category}} pq"]'],
                )
                head_args += [*site_args, '--range', pq_value, ]
                args = MultiList([[*head_args, url + f' {s}'] for s in site_settings['sort_tag_list']])
            elif os.path.isdir(pq_value):
                override_base_dir, target_dir = os.path.split(pq_value.strip(r'\/"').strip(r'\/"'))
                post_id_l = []
                for i in os.listdir(pq_value):
                    # m = re.search(r'\d\d\d\d-\d\d-\d\d (\w+) ', i)
                    m = re.search(r' ([0-9a-f]{32}) ', i)
                    if m:
                        post_id_l.append(m.group(1))
                url_l = [f'https://{site_host}{post_path_prefix}{post_id}' for post_id in post_id_l]
                # url_l = [f'https://{site_host}/posts?tags=md5:{post_id}' for post_id in post_id_l]
                args = [
                    *GLDLCLIArgs(
                        o=[
                            *options,
                            f'base-directory={override_base_dir}',
                            f'directory=["{target_dir}"]',
                            'image-filter=""',
                        ],
                    ),
                    *site_args, *url_l,
                ]
            elif pq_value[0] == '+' and os.path.isdir(pq_value[1:]):
                the_path = pq_value[1:].strip(r'\/"').strip(r'\/"')
                override_base_dir, target_dir = os.path.split(the_path)
                url = f'https://{site_host}{tag_path_prefix}{target_dir.split(site_name)[0].strip()}'
                head_args = GLDLCLIArgs(
                    *site_args,
                    o=[
                        *options,
                        f'base-directory={override_base_dir}',
                        f'directory=["{target_dir}"]',
                        # '''image-filter="md5 not in FILTER_SET['not_want']['md5']"'''
                    ]
                )
                if target_dir[-3:] == ' pq':
                    pq_num = len([i for i in os.listdir(the_path) if i[-len(STRING_NOT_WANT):] != STRING_NOT_WANT]) // 3
                    head_args += ['--range', f'1-{pq_num}', ]
                    args = MultiList([[*head_args, url + f' {s}'] for s in site_settings['sort_tag_list']])
                else:
                    args = head_args + [url, ]
    return args


def pop_tag_from_args(args):
    return fstk.sanitize_xu(re.sub(r'[\[\]]', '', args.pop(0)), reverse=True,
                            unescape_html=False, decode_url=False, unify_white_space=False)


def args2url(args):
    first = args.pop(0)
    if first in ('pixiv', 'p'):
        url = 'https://www.pixiv.net'
    elif first == 'fanbox':
        url = f'https://{args.pop(0)}.fanbox.cc'
    elif first == 'twitter':
        url = f'https://twitter.com/{args.pop(0).lstrip("@")}/media'
    elif first == 'danbooru':
        url = f'https://danbooru.donmai.us/posts?tags={pop_tag_from_args(args)}'
    elif first in ('gelbooru', 'gel'):
        # todo#mark gelbooru
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
            url = f'https://chan.sankakucomplex.com/posts/{x}'
        elif not x:
            url = 'https://chan.sankakucomplex.com'
        else:
            url = f'https://chan.sankakucomplex.com/?tags={x}'
    elif first in ('idol', 'idolcomplex'):
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://idol.sankakucomplex.com/posts/{x}'
        elif x[:3] == 'id=':
            url = f'https://idol.sankakucomplex.com/posts/{x[3:]}'
        elif not x:
            url = 'https://idol.sankakucomplex.com'
        else:
            url = f'https://idol.sankakucomplex.com/?tags={x}'
    elif first in ('ng', 'newgrounds'):
        url = f'https://{pop_tag_from_args(args)}.newgrounds.com/art'
    # todo#mark kemono
    elif first in ('kemono', 'kemonoparty', 'kemono.su'):
        x = pop_tag_from_args(args)
        if os.path.isfile(x):
            url = 'kemono.'
            args[:0] = ['-i', x]
        elif x in ('patreon', 'fanbox', 'fantia'):
            y = pop_tag_from_args(args)
            url = f'https://kemono.su/{x}/user/{y}'
        else:
            url = f'https://kemono.su/{pop_tag_from_args(args)}'
    elif first in ('coomer', 'coomerparty', 'coomer.su'):
        x = pop_tag_from_args(args)
        if os.path.isfile(x):
            url = 'coomer.'
            args[:0] = ['-i', x]
        elif x in ('onlyfans', 'fansly'):
            y = pop_tag_from_args(args)
            url = f'https://coomer.su/{x}/user/{y}'
        else:
            url = f'https://coomer.su/{pop_tag_from_args(args)}'
    elif first in ('luscious', 'lus'):
        x = pop_tag_from_args(args)
        if re.match(r'\d+ \d+', x):
            a, b = x.split()
            url = f'https://www.luscious.net/pictures/album/{a}/id/{b}'
        else:
            url = f'https://www.luscious.net/albums/{x}'
            import browser_cookie3
            url = requests.get(url, cookies=browser_cookie3.firefox()).url
    elif first in ('reddit',):
        p = r'\w+'
        v1 = pop_tag_from_args(args)
        if re.fullmatch('u_' + p, v1):
            v1 = f'user/{v1[2:]}'
        elif re.fullmatch(p, v1):
            v1 = f'r/{v1}'
        if args:
            v2 = pop_tag_from_args(args)
            if re.fullmatch(r'pq[\d-]+', v2):
                url = f'https://www.reddit.com/{v1}'
                args.insert(0, v2)
            elif re.fullmatch(r'[a-z0-9]{5,}', v2):
                url = f'https://www.reddit.com/{v1}/comments/{v2}'
            else:
                url = f'https://www.reddit.com/{v1}'
                args.insert(0, v2)
        else:
            url = f'https://www.reddit.com/{v1}'
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
    if 'reddit.com' in url and '/s/' in url:
        import browser_cookie3
        url = requests.get(url, cookies=browser_cookie3.firefox()).url
        print(url)
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
            if 'hitomi.la' in line:
                line = line.strip('"')
                line = f'"{line}"'
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
        need_pause = False
        for cmd in cmd_l:
            try:
                print(cmd)
                p = subprocess.Popen(cmd)
                # print(p.args)
                if p.wait() and pause_on_error:
                    need_pause = True
            except KeyboardInterrupt:
                sys.exit(2)
        if need_pause:
            console_pause()


if __name__ == '__main__':
    main()
