#!/usr/bin/env python3
import os.path
import string
import webbrowser

import requests

from mylib.ext.console_app import *

# if os.name != 'nt':
#     raise NotImplementedError('launch new console window')

STRING_NOT_WANT = '.not_want'

env_var = os.environ
base_dir = fstk.make_path(env_var['gallery_dl_base_directory']).strip('"')
pause_on_error = os.environ.get('PAUSEONERROR', 'yes').lower() in {
    'yes', 'true', '1'}


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


class RuntimeData:
    flag_need_more_specific_url: bool


def per_site(args: T.List[str]):
    url = args2url(args)
    # TODO: mark pixiv
    if 'pixiv.net' in url:
        gldl_args = GLDLCLIArgs(
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
                more_args = [
                    '-o', 'extractor.pixiv.include=["background","avatar"]']
                if '/users/' in url:
                    gldl_args.extend([*args[1:], *more_args, url])
                else:
                    url = f'https://www.pixiv.net/users/{args[1]}'
                    gldl_args.extend([*args[2:], *more_args, url])
            elif arg0 in ('u', 'user'):
                url = f'https://www.pixiv.net/users/{args[1]}'
                gldl_args.extend([*args[2:], url])
            elif arg0 in ('a', 'art', 'artwork'):
                url = f'https://www.pixiv.net/artworks/{args[1]}'
                gldl_args.extend([*args[2:], url])
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
        # TODO: mark danbooru
        site_name = 'danbooru'
        site_host = 'danbooru.donmai.us'
        options = [
            'filename="{category} {created_at:.10} {id} {md5}'
            ' {tag_string_character!S:X64/.../}'
            ' $ {tag_string_copyright!S:X32/.../}'
            ' @ {tag_string_artist!S:X32/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' order:rank', ' order:curated', ' order:score', ' order:favcount', ' order:upvotes'],
            'tag_path_prefix': '/posts?tags=',
            'post_path_prefix': '/posts/',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'gelbooru.com' in url:
        # TODO: mark gelbooru
        # sort 目前能进行质量排序的 只有 score
        # 会从 danbooru 抓取 但后续的tag编辑 不会更新抓取
        site_name = 'gelbooru'
        site_host = 'gelbooru.com'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tags_character!S:X64/.../}'
            ' $ {tags_copyright!S:X32/.../}'
            ' @ {tags_artist!S:X32/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' sort:score', ('', 0.2)],
            'tag_path_prefix': '/index.php?page=post&s=list&tags=',
            'post_path_prefix': '/index.php?page=post&s=view&id=',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'aibooru.online' in url:
        # TODO: mark aibooru
        site_name = 'aibooru'
        site_host = 'aibooru.online'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tag_string_character!S:X64/.../}'
            ' $ {tag_string_copyright!S:X32/.../}'
            ' @ {tag_string_artist!S:X32/.../} {tag_string_model!S:X32/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' order:rank', ' order:rank2', ' order:views', ' order:score', ' order:favcount'],
            'tag_path_prefix': '/posts?tags=',
            'post_path_prefix': '/posts/',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'rule34.xxx' in url:
        site_name = 'rule34'
        site_host = 'rule34.xxx'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tags_character!S:X64/.../}'
            ' $ {tags_copyright!S:X32/.../}'
            ' @ {tags_artist!S:X32/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' sort:score', ('', 0.2)],
            'tag_path_prefix': '/index.php?page=post&s=list&tags=',
            'post_path_prefix': '/index.php?page=post&s=view&id=',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'realbooru.com' in url:
        site_name = 'realbooru'
        site_host = 'realbooru.com'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' $ {tags_copyright!S:X64/.../}'
            ' @ {tags_model!S:X64/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' sort:score', ('', 0.2)],
            'tag_path_prefix': '/index.php?page=post&s=list&tags=',
            'post_path_prefix': '/index.php?page=post&s=view&id=',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'chan.sankakucomplex.com' in url:
        # TODO: mark sankaku
        site_name = 'sankaku'
        site_host = 'chan.sankakucomplex.com'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tag_string_character!S:X40/.../}'
            ' $ {tag_string_copyright!S:X32/.../} {tags_studio!S:X32/.../}'
            ' @ {tag_string_artist!S:X32/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' order:popular', ' order:quality'],
            'tag_path_prefix': '/?tags=',
            'post_path_prefix': '/posts/',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

    elif 'idol.sankakucomplex.com' in url:
        site_name = 'idolcomplex'
        site_host = 'idol.sankakucomplex.com'
        options = [
            'filename="{category} {date!S:.10} {id} {md5}'
            ' {tags_genre!S:X32/.../}'
            ' $ {tags_copyright!S:X32/.../} {tags_studio!S:X32/.../}'
            ' @ {tags_artist!S:X40/.../}'
            ' .{extension}"',
        ]
        site_settings = {
            'sort_tag_list': [' order:popular', ' order:quality'],
            'tag_path_prefix': '/?tags=',
            'post_path_prefix': '/posts/',
        }
        gldl_args = pq_site_arg_func(
            options, args, site_host, site_name, url, site_settings)

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
                    [*GLDLCLIArgs(), *args, f'--range',
                     f'1-{pq_value}', url + '?order=trending'],
                    [*GLDLCLIArgs(), *args, f'--range',
                     f'1-{pq_value}', url + '?order=best'],
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
                                     '{title} @{artist!S:X80/.../} .{extension}"', ]),
                     *args, url]
    elif 'kemono.' in url or 'coomer.' in url:
        # TODO: mark kemono
        _arg_in_list = []
        _filter_sequence_in_list = []
        for a in args:
            word = 'filter+'
            if a.startswith(word):
                _filter_sequence_in_list.append(a.removeprefix(word))
                continue
            _arg_in_list.append(a)
        args = _arg_in_list
        gldl_args = [
            *GLDLCLIArgs(
                o=[
                    'cookies-update=true', 'videos=true', 'tags=true', 'metadata=true',
                    'directory=["{username} {category} {service} {user}"]',
                    'filename="{category} {service} {date!S:.10} {id} {title:.60} {count}p '
                    '@{username} p{num} {filename:.40}.{extension}"',
                ],
                filter=' and '.join([
                    "extension not in ('psd', 'clip')",
                    *_filter_sequence_in_list
                ]),
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

    return url, gldl_args


def pq_value_to_range_value(pq_value: str | int, k_factor):
    if isinstance(pq_value, str):
        if '-' in pq_value:
            return pq_value
        pq_value = int(pq_value)
    if isinstance(pq_value, int):
        return f'1-{int(pq_value * k_factor)}'
    raise TypeError(pq_value)


def add_sort_range_args(common_args, pq_value, url, site_settings):
    r = MultiList()
    for sort_and_k in site_settings['sort_tag_list']:
        if isinstance(sort_and_k, str):
            sort_tag = sort_and_k
            k_factor = 1
        elif isinstance(sort_and_k, tuple):
            sort_tag, k_factor = sort_and_k
        else:
            raise TypeError(sort_and_k)
        r.append([*common_args, '--range',
                 pq_value_to_range_value(pq_value, k_factor), url + sort_tag])
    return r


def pq_site_arg_func(options, site_args, site_host, site_name, url, site_settings):
    post_path_prefix = site_settings['post_path_prefix']
    tag_path_prefix = site_settings['tag_path_prefix']
    gldl_args = [
        *GLDLCLIArgs(
            o=[
                *options,
                'directory=["{search_tags!S:R  / /} {category}"]'
            ],
        ),
        *site_args, url
    ]
    if site_args:
        tags_s = url.split(
            tag_path_prefix, maxsplit=1)[-1].strip().replace('  ', ' ')
        pq_arg, *site_args = site_args
        if pq_arg.startswith('pq'):
            pq_value = pq_arg[2:]
            if set(pq_value) <= set(string.digits + '-'):
                head_args = GLDLCLIArgs(
                    o=[*options, f'directory=["{tags_s} {{category}} pq"]'],
                )
                gldl_args = add_sort_range_args(
                    [*head_args, *site_args], pq_value, url, site_settings)

            elif pq_value[0] == '=' and os.path.isdir(pq_value[1:]):
                the_path = pq_value[1:].strip(r'\/"').strip(r'\/"')
                override_base_dir, target_dir = os.path.split(the_path)
                post_id_l = []
                for i in os.listdir(the_path):
                    if 'sankaku' in site_host:
                        m = re.search(r' ([0-9a-f]{32}) ', i)
                    else:
                        m = re.search(r'\d\d\d\d-\d\d-\d\d (\w+) ', i)
                    if m:
                        post_id_l.append(m.group(1))
                url_l = [
                    f'https://{site_host}{post_path_prefix}{post_id}' for post_id in post_id_l]
                # url_l = [f'https://{site_host}/posts?tags=md5:{post_id}' for post_id in post_id_l]
                gldl_args = [
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
                search_tag_string = fstk.sanitize_xu(
                    target_dir.split(site_name)[0].strip(), reverse=True)
                url = f'https://{site_host}{tag_path_prefix}{search_tag_string}'
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
                    pq_value = len([i for i in os.listdir(
                        the_path) if not i.endswith(STRING_NOT_WANT)]) // 5
                    gldl_args = add_sort_range_args(
                        head_args, pq_value, url, site_settings)
                else:
                    gldl_args = head_args + [url, ]

                args_txt_filepath = os.path.join(the_path, 'args.txt')
                if os.path.isfile(args_txt_filepath):
                    with open(args_txt_filepath, 'r') as f:
                        args_list = f.read().strip().split('\n')
                    args_list = [i.strip() for i in args_list]
                    if isinstance(gldl_args, MultiList):
                        for _l in gldl_args:
                            _l.extend(args_list)
                    else:
                        gldl_args.extend(args_list)
    return gldl_args


def pop_tag_from_args(args):
    return fstk.sanitize_xu(re.sub(r'[\[\]]', '', args.pop(0)), reverse=True,
                            unescape_html=False, decode_url=False, unify_white_space=False)


def process_arg_list(arg_l: list):
    for k, v in {
        '!idl': ['~video', '~animated_gif'],
        '!idl-v': ['-video', '-animated_gif'],
        '!rl-v': '-video -animated -gif -webm -mp4',
    }.items():
        if k in arg_l:
            i = arg_l.index(k)
            if isinstance(v, str):
                v = v.split()
            if not isinstance(v, list):
                v = list(v)
            arg_l[i:i+1] = v

    token = '.'
    if token in arg_l:
        i = arg_l.index(token)
        slice_before_token = arg_l[:i]
        slice_before_token = ' '.join(slice_before_token)
        arg_l[:i + 1] = [slice_before_token]

    # print(arg_l)


def args2url(args):
    special = '{o:ab}'
    if special in args:
        i = args.index(special)
        args[i:i + 1] = ['-o', 'include=["background","avatar"]']
    first = args.pop(0)
    if first in ('pixiv', 'p'):
        url = 'https://www.pixiv.net'
        RuntimeData.flag_need_more_specific_url = True
    elif first in ('civitai', 'cvai'):
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://civitai.com/images/{x}'
    elif first == 'fanbox':
        url = f'https://{args.pop(0)}.fanbox.cc'
    elif first == 'twitter':
        url = f'https://twitter.com/{args.pop(0).lstrip("@")}/media'
    elif first in ('danbooru', 'dan',):
        # TODO: mark danbooru
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://danbooru.donmai.us/posts/{x}'
        else:
            url = f'https://danbooru.donmai.us/posts?tags={x}'
    elif first in ('gelbooru', 'gel'):
        # TODO: mark gelbooru
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://gelbooru.com/index.php?page=post&s=view&id={x}'
        else:
            url = f'https://gelbooru.com/index.php?page=post&s=list&tags={x}'
    elif first in ('rule34', 'r34'):
        # TODO: mark gelbooru
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://rule34.xxx/index.php?page=post&s=view&id={x}'
        else:
            url = f'https://rule34.xxx/index.php?page=post&s=list&tags={x}'
    elif first in ('realbooru', 'real', 'rl'):
        # TODO: mark realbooru
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit():
            url = f'https://realbooru.com/index.php?page=post&s=view&id={x}'
        else:
            url = f'https://realbooru.com/index.php?page=post&s=list&tags={x}'
    elif first in ('sankaku', 'chan', 'skk', 'c'):
        process_arg_list(args)
        x = pop_tag_from_args(args)
        # if x.isdigit() or re.fullmatch(r'[0-9a-z]{32}', x):
        #     url = f'https://chan.sankakucomplex.com/posts/{x}'
        if x[:3] == 'id=':
            url = f'https://chan.sankakucomplex.com/posts/{x[3:]}'
        elif not x:
            url = 'https://chan.sankakucomplex.com'
        else:
            url = f'https://chan.sankakucomplex.com/?tags={x}'
    elif first in ('idol', 'idolcomplex', 'idl', 'i'):
        process_arg_list(args)
        x = pop_tag_from_args(args)
        if x.isdigit() or re.fullmatch(r'[0-9a-z]{32}', x):
            url = f'https://idol.sankakucomplex.com/posts/{x}'
        elif x[:3] == 'id=':
            url = f'https://idol.sankakucomplex.com/posts/{x[3:]}'
        elif not x:
            url = 'https://idol.sankakucomplex.com'
        else:
            url = f'https://idol.sankakucomplex.com/?tags={x}'
    elif first in ('ng', 'newgrounds'):
        url = f'https://{pop_tag_from_args(args)}.newgrounds.com/art'
    # TODO: mark kemono
    elif first in ('kemono', 'kemonoparty', 'kemono.su'):
        x = pop_tag_from_args(args)
        if os.path.isfile(x):
            url = 'kemono.'
            args[:0] = ['-i', x]
        elif x in ('patreon', 'fanbox', 'fantia', 'gumroad'):
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
    elif first in ('reddit', 'rdt'):
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
    elif first in ('redgifs', 'rdg'):
        url = f'https://www.redgifs.com/gifs/{pop_tag_from_args(args)}'
    elif first in ('ai', 'aibooru',):
        # TODO: mark aibooru
        process_arg_list(args)
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
    url = url.replace('chan.sankakucomplex.com/cn/',
                      'chan.sankakucomplex.com/')
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
    if args:
        arg0 = args[0]
        if not arg0.startswith('https://') and ' ' in arg0:
            args[0:1] = arg0.split()
    ostk.set_console_title(f'{path_basename(__file__)} - {args}')
    if not args:
        loop()
    else:
        if args[0] == 'o':
            args.pop(0)
            url, _ = per_site(args)
            return webbrowser.open_new_tab(url)
        url, site_args = per_site(args)
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
                ostk.set_console_title('')
                sys.exit(2)
        if need_pause:
            console_pause()
    ostk.set_console_title('')


if __name__ == '__main__':
    main()
