import webbrowser
from functools import reduce

import mylib.__deprecated__
from mylib.ext.fstk import *
from mylib.ext.fstk import read_sqlite_dict_file
from mylib.ext.ostk import clipboard as cb
from mylib.ext.text import *
from mylib.ext.tui import *
from mylib.easy import split_path_dir_base_ext

src = r'd:\usr\dl\1'
ref = r'd:\usr\dl\HentaiNexus metadata'
dst = r'U:\priv\h\_hentainexus'

db = defaultdict(set)
lp = LinePrinter()
webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(r'C:\Program Files\Mozilla Firefox\firefox.exe'))
firefox = webbrowser.get('firefox')


def parse_copied_fakku_info(text: str):
    d = {}
    lines = [l for l in text.splitlines() if l]
    title = d['title'] = lines[0]
    lines_iter = iter(lines[1:])
    for k, v in zip(lines_iter, lines_iter):
        d[k] = v
    d['various'] = False
    long_title = ''
    event = d.get('Event')
    if event:
        long_title += f'({event}) '
    artist = d['Artist']
    if artist.count(',') > 2:
        artist = 'Various'
        d['various'] = True
    circle = d.get('Circle')
    if circle:
        long_title += f'[{circle} ({artist})] '
    else:
        long_title += f'[{artist}] '
    long_title += title
    parody = d['Parody']
    if parody != 'Original Work':
        long_title += f' ({parody})'
    book = d.get('Book')
    if book:
        long_title += f' ({book})'
    magazine = d.get('Magazine')
    if magazine:
        long_title += f' ({magazine})'
    long_title += f''' [{d['Language']}][{d['Publisher']}]'''
    d['long_title'] = long_title
    return d


'''
for fp in find_iter('f', ref, relative_to=ref):
    folder, name, _ = split_dirname_basename_ext(fp)
    core_title = re.sub(r'(.+?]) ([^\[\]()]+) (\(|\[).+', r'\1 \2', name)
    # print(core_title)
    os.makedirs(make_path(dst, folder), exist_ok=True)
    words = find_words(core_title.lower())
    for w in words:
        db[w].add(make_path(dst, folder, name + '.cbz'))

write_sqlite_dict_file(ref + '.db', db)
'''

db = read_sqlite_dict_file(ref + '.db')


def prompt_rename(fp):
    bn = os.path.basename(fp)
    cb.clear()
    noext = os.path.splitext(bn)[0]
    cb.set(noext)
    firefox.open_new(f'https://www.google.com/search?q={" ".join(find_words(noext))}')
    given = prompt_input(f'MOVE: {fp}{CRLF}')
    if given == 'cb':
        info = parse_copied_fakku_info(cb.get())
        artist = info['Artist']
        circle = info.get('Circle')
        if ',' in artist:
            if circle and ',' not in circle:
                folder = f'[{circle}]'
            else:
                folder = '[(various)]'
        else:
            folder = f'[{artist}]'
        given = make_path(folder, info['long_title'] + '.cbz')
    if given == 'as':
        m1 = re.match(r'(\(.+?\) )\[(.+?) \((.+?)\)\] .+', bn)
        m2 = re.match(r'\[(.+?)] .+', bn)
        if m1:
            _, circle, artist = m1.groups()
            if artist == 'Various':
                if ',' in circle:
                    folder = '[(various)]'
                else:
                    folder = f'[{circle}]'
            else:
                folder = f'[{artist}]'
        if m2:
            artist = m2.group(1)
            folder = f'[{artist}]'
        given = make_path(folder, bn)
    given_dirname, given_basename = given.split(os.path.sep, maxsplit=1)
    new = make_path(dst, make_path(given_dirname, given_basename, part_converter=sanitize_xu))
    os.makedirs(os.path.dirname(new), exist_ok=True)
    try:
        print(f'{new} <- {fp}')
        mylib.__deprecated__.move_safe___alpha(fp, new)
    except FileExistsError:
        print(f'! {fp}')
        cb.set(split_path_dir_base_ext(new)[1])
        sys.exit()


# '''
for fp in find_iter('f', src):
    _, name, _ = split_path_dir_base_ext(fp)
    core_title = re.sub(r'(.+?]) ([^\[\]()]+) (\(|\[).+', r'\1 \2', name)
    # print(core_title)
    words0 = find_words(core_title.lower())
    words = [str(int(w)) if w.isdecimal() else w for w in words0]
    # print(words)
    possible_sets = [db[w] for w in words if w in db]
    try:
        intersection = reduce(lambda x, y: x & y, possible_sets)
    except TypeError:
        prompt_rename(fp)
        continue
    # print(intersection)
    intersection = sorted(intersection, key=lambda x: len(set(find_words(x)) & set(find_words(fp))), reverse=True)
    if not intersection:
        prompt_rename(fp)
        continue
    first = intersection[0]
    first_words = find_words(re.sub(r'(.+?]) ([^\[\]()]+) (\(|\[).+', r'\1 \2', os.path.basename(first).lower()))
    if len(intersection) == 1 and first_words == words0:
        new = intersection[0]
    else:
        # continue
        lp.l()
        new = prompt_choose_number(f'MOVE {fp}', intersection)
    if not new:
        lp.l()
        prompt_rename(fp)
    else:
        try:
            d, b = os.path.split(new)
            new = make_path(d, sanitize_xu(b))
            print(f'{new} <- {fp}')
            mylib.__deprecated__.move_safe___alpha(fp, new)
        except FileExistsError:
            print(f'! {fp}')
            cb.set(split_path_dir_base_ext(new)[1])
            sys.exit()
# '''
