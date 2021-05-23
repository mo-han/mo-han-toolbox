ytdl.sh.cmd
```shell script
#!/bin/sh
mykit ytdl -- $* 2>&1 || exit 3
```

 .config/youtube-dl/config
```shell script
-o "%(title).70s [%(id)s][%(uploader)s].%(ext)s"
--yes-playlist
--fragment-retries infinite
-icw
--external-downloader aria2c
--external-downloader-args "-x10 -s10 -k 1M"
-f (299/137)[height<=?1080][fps<=60]+(m4a/aac)/bestvideo+bestaudio/best
```

bldl.sh.cmd
```shell script
#!/bin/sh
mykit bldl -c .config/cookies.bilibili.txt $* 2>&1 || exit 3
```

tree2path.py
```python
"""convert fs tree to full path (from stdin)"""
import sys

HEAD = '│   '
TAIL = '── '
IGNORE_DIR = True

parts = []
for line in sys.stdin:
    clean_line = line.rstrip('\n').encode(errors='surrogateescape', encoding='ansi').decode()
    name = clean_line.split(TAIL)[-1]
    is_dir = name.endswith('/')
    if is_dir:
        name = name[:-1]
    indent = clean_line.count(HEAD)
    parts = [*parts[:indent], name]
    if is_dir and IGNORE_DIR:
        continue
    print('/'.join(parts))
```


微信 盛言奉天城韵 配音视频
```python
import lxml.html
import splinter

from mylib.easy import *
from mylib.wrapper import aria2c

b = splinter.browser.FirefoxWebDriver(headless=True)


def visit_util_title(url):
    b.visit(url)
    while not b.title:
        sleep(.1)


def visit_blank():
    b.visit('about:blank')
    while b.html != '<html><head></head><body></body></html>' or b.title:
        sleep(.1)


home = ''
b.visit(home)
ht = lxml.html.fromstring(b.html)
pages = {i.attrib['href'] for i in ht.xpath('//section/section/a')}
pages = sorted(pages)
for page in pages:
    visit_blank()
    visit_util_title(page)
    title = b.title
    if not title:
        raise RuntimeError(repr(title), page)
    print(title)
    print(page)
    ht = lxml.html.fromstring(b.html)
    for i, v in enumerate(ht.find_class('video_fill'), 1):
        v_url = v.attrib['origin_src']
        fp = f'{title} {i}.mp4'
        print(fp)
        print(v_url)
        aria2c.run_aria2c(v_url, o=fp)
```