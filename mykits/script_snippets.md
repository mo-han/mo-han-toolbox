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
mykit bldl -c .config/cookies.bilibili.txt $* 2>&1 || exit 3
```