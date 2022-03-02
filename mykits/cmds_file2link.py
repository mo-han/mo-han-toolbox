#!/usr/bin/env python3
import ezpykit.enhance_stdlib.re
from mylib.ext.console_app import *

import webbrowser

apr = ArgumentParserWrapper()
an = apr.an
an.s = an.src = an.B = an.not_browse = ''


@apr.sub()
@apr.opt(an.s, an.src, nargs='*')
@apr.true(an.B, apr.dst2opt(an.not_browse))
@apr.map(an.src, an.not_browse)
def post_id(fp_list, not_browse):
    sites_post_url_fmt = {
        'sankaku': 'https://chan.sankakucomplex.com/post/show/{}',
        'pixiv': 'https://www.pixiv.net/artworks/{}',
        'danbooru': 'https://danbooru.donmai.us/posts/{}',
        'gelbooru': 'https://gelbooru.com/index.php?page=post&s=view&id={}',
        'idolcomplex': 'https://idol.sankakucomplex.com/post/show/{}',
        'twitter': 'https://twitter.com/twitter/statuses/{}',
    }
    urls_l = []
    for bn in map(path_basename, resolve_path_to_dirs_files(fp_list)[1] or ostk.clipboard.get().splitlines()):
        print(f'@ {bn}')
        words = ezpykit.enhance_stdlib.re.find_words(bn, allow_mix_non_word_chars='-')
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
                id_num = int(w)
            elif m2:
                id_num = int(m2.groups()[0])
            else:
                continue
            url = url_fmt.format(id_num)
            urls_l.append(url)
            print(f'* {url}')
            if not not_browse:
                webbrowser.open_new_tab(url)
            break
    if not_browse:
        ostk.clipboard.set('\r\n'.join(urls_l))


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
