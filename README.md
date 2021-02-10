#### [SubscriptableFileIO](mylib/os_auto.py#L274)

read/write file with slice

切片式文件读写

```python

from mylib.os_lite import SubscriptableFileIO
with SubscriptableFileIO('filepath') as f:
    f[-10:] = b'123abc'
    print(f[123:456])
```

#### [Simple Telegram Bot](mylib/tg_bot.py#L35)

a very easy-to-use and write-less-do-more wrapper class of [PTB](https://github.com/python-telegram-bot/python-telegram-bot/ 'python-telegram-bot')

make a Telegram bot like this:

```python
from mylib.tg_bot import SimpleBot, meta_deco_handler_method
from telegram.ext import CommandHandler
class MyBot(SimpleBot):
    @meta_deco_handler_method(CommandHandler)
    def hello(self, update, context):
        """say hi"""
        self.__typing__(update)
        update.message.reply_text('Hi!')
bot = MyBot('TOKEN', auto_run=False)
bot.__run__()
```

#### [bilibili_aocx](mykits/bilibili_aocx.py)

bilibili APP offline cache extractor

B站 移动端应用 离线缓存 提取器

bilibili mobile client APP offline cache extractor

[.exe pre-release](https://github.com/mo-han/mo-han-toolbox/releases/download/t0/bilibili_aocx.exe)

#### [mykit.py](mykits/mykit.py)

self-using multifunctional script

自用多功能脚本

some of the functions (sub commands):

##### wrap.ffmpeg (aliases: ffmpeg, ff)

a ffmpeg wrapper, can get source file(s) from clipboard

`mykit ff -k smallhd` equivalent to `ffmpeg -pix_fmt yuv420 -c:v hevc -crf 25` and scale down resolution into HD (1280x720)

##### wrap.ffprobe (aliases: ffprobe, ff)

a ffprobe wrapper, can get source file(s) from clipboard

`mykit fp` will print info of filepath in clipboard

#### [DownloadPool](mylib/web_client.py#L336)

HTTP multi-threading downloader

```python
from mylib.web_client import DownloadPool
url = ...
file = ...
retry = ...
d = DownloadPool()
d.submit_download(url, file, retry, cookies=...)
d.put_download_in_queue(url, file, retry, cookies=...)
d.put_end_of_queue()
d.start_queue_loop()
```

#### [PotPlayerKit](mylib/potplayer.py)

toolkit for PotPlayer.
main features in current version:
- find opened PotPlayer window and bring it to foreground
- get and parse info of the opened media file
- rename/move the opened media file
- a [GUI dialog](mylib/gui_old.py#L44) to rename/move the opened media file

#### [VoidDuck](mylib/tricks.py#L141)

虚空之鸭，万能的鸭鸭，无能的鸭鸭，随你怎么对待它，鸭鸭不反抗，鸭鸭不回答

a void, versatile, useless and quiet duck, called anyhow, no return no raise

#### [PixivFanboxAPI](mylib/site_pixiv.py#L71)

pixivFANBOX API (incomplete but usable)

- api
    - get_post_info
    - get_creator_info
    - list_post_of_creator
    - list_sponsor_plan_of_creator
- download
    - download_pixiv_fanbox_post
    - download_pixiv_fanbox_creator
