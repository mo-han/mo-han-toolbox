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