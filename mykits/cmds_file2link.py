#!/usr/bin/env python3
from mylib.ex.console_app import *

import webbrowser

apr = ArgumentParserRigger()
an = apr.an
an.s = an.src = ''


@apr.sub()
@apr.opt(an.s, an.src, nargs='*')
@apr.map(an.src)
def post_id(fp_list):
    sites_post_url_fmt = {
        'sankaku': 'https://chan.sankakucomplex.com/post/show/{}',
        'pixiv': 'https://www.pixiv.net/artworks/{}',
        'danbooru': 'https://danbooru.donmai.us/posts/{}',
        'gelbooru': 'https://gelbooru.com/index.php?page=post&s=view&id={}',
        'idolcomplex': 'https://idol.sankakucomplex.com/post/show/{}',
        'twitter': 'https://twitter.com/twitter/statuses/{}',
    }
    for bn in map(path_basename, resolve_path_to_dirs_files(fp_list)[1] or ostk.clipboard.get().splitlines()):
        print(f'@ {bn}')
        words = text.find_words(bn, allow_mix_non_word_chars='-')
        intersect = set(words) & set(sites_post_url_fmt.keys())
        if not intersect:
            continue
        if len(intersect) > 1:
            print(f'# {bn}')
            continue
        site_name = intersect.pop()
        url_fmt = sites_post_url_fmt[site_name]
        for w in words:
            # print(f': {w}')
            if w == site_name:
                continue
            m1 = re.fullmatch(r'\d+', w)
            m2 = re.fullmatch(r'(\d+)(?:[_-])p?(\d+)', w)
            if m1:
                post_id = int(w)
            elif m2:
                post_id = int(m2.groups()[0])
            else:
                continue
            url = url_fmt.format(post_id)
            print(f'* {url}')
            webbrowser.open_new_tab(url)
            break


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
