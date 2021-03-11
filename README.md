
Table of Contents
=================

* [<a href="/blob/fd4ffad4be682ea248f8b8550c8538b7ff4f7004/mylib/ez/\_\_init\_\_\.py\#L35">AttrName</a>](#attrname)
* [<a href="/blob/3bafdf4e8d5267a9071523e4046c39892c3a20d0/mylib/ez/argparse\.py\#L28">ArgumentParserRigger</a>](#argumentparserrigger)
* [<a href="mylib/ostk\.py\#L274">SubscriptableFileIO</a>](#subscriptablefileio)
* [<a href="mylib/tg\_bot\.py\#L35">Simple Telegram Bot</a>](#simple-telegram-bot)
* [<a href="mykits/bilibili\_aocx\.py">bilibili\_aocx</a>](#bilibili_aocx)
* [<a href="mykits/mykit\.py">mykit\.py</a>](#mykitpy)
  * [wrap\.ffmpeg (aliases: ffmpeg, ff)](#wrapffmpeg-aliases-ffmpeg-ff)
  * [wrap\.ffprobe (aliases: ffprobe, ff)](#wrapffprobe-aliases-ffprobe-ff)
* [<a href="mylib/web\_client\.py\#L336">DownloadPool</a>](#downloadpool)
* [<a href="mylib/shards/potplayer\.py">PotPlayerKit</a>](#potplayerkit)
* [<a href="mylib/tricks\.py\#L141">VoidDuck</a>](#voidduck)
* [<a href="mylib/sites/pixiv\.py\#L71">PixivFanboxAPI</a>](#pixivfanboxapi)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc.go)


#### [AttrName](/blob/fd4ffad4be682ea248f8b8550c8538b7ff4f7004/mylib/ez/__init__.py#L35)

its attribute is a str same as the name thereof

实例的属性总是一个和属性名称相同的字符串

```python
from mylib.ez import AttrName

an = AttrName()
assert an.abc_xyz == 'abc_xyz'
an.abc_xyz = 123456  # nothing happens
```

#### [ArgumentParserRigger](/blob/3bafdf4e8d5267a9071523e4046c39892c3a20d0/mylib/ez/argparse.py#L28)

use argparse in @decorator style

通过装饰器来使用argparse

features:
- full decorating style for adding arguments or sub-commands;
- user-defined mapping from arguments to parameters (of the decorated function);
- the decorated function remains untouched;
- thus the decorated function can be re-used anywhere as though it was never argparse-decorated;
- the rigger knows which function is to be called and how to call it.

```python
# test.py
from mylib.ez.argparse import *
from mylib.ez import AttrName

pr = ArgumentParserRigger()
ro = RawObject  # ro(x) -> RawObject(x), RawObject(x).value == x
an = AttrName()  # an.abc_xyz == 'abc_xyz'
an.x = an.y = an.z = an.l = ''  # let the IDE remember these attr names


@pr.sub_command(lambda x: x.replace('_', '-'))  # xyz_and_more -> xyz-and-more
@pr.argument(an.x)
@pr.argument(an.y)
@pr.argument(an.z)
# flag means option with action='store_true', so the flag 'l' means option '-l'
@pr.flag(an.l, help='print in multiple lines')
# arg x -> param x, arg z -> param z, int(1111) -> param y, unknown_args -> param y, flag -l -> param multi_line
@pr.map_target_signature(an.x, ro(1111), an.z, UnknownArguments(), multi_line=an.l)
def xyz_and_more(x, y, z, more, multi_line=False):
    print(f'x={x}', f'y={y}', f'z={z}', f'and more: {", ".join(more)}', sep='\n' if multi_line else ', ')


@pr.sub_command()
@pr.argument('a')
@pr.argument('b')
@pr.map_target_signature('a', 'b')
def ab(a, b):
    print(a, b)


pr.parse_known_args()
pr.run_target()
```

```
> test -h
usage: test.py [-h] {xyz-and-more,ab} ...

positional arguments:
  {xyz-and-more,ab}

optional arguments:
  -h, --help         show this help message and exit

> test ab -h
usage: test.py ab [-h] a b

positional arguments:
  a
  b

optional arguments:
  -h, --help  show this help message and exit

> test xyz-and-more -h
usage: test.py xyz-and-more [-h] [-l] x y z

positional arguments:
  x
  y
  z

optional arguments:
  -h, --help  show this help message and exit
  -l          print in multiple lines

> test xyz-and-more 0 0 0 a b c
x=0, y=1111, z=0, and more: a, b, c

> test xyz-and-more 0 0 0 a b c -l
x=0
y=1111
z=0
and more: a, b, c

> test ab 1 2
1 2
```

#### [SubscriptableFileIO](mylib/ostk.py#L274)

read/write file with slice

切片式文件读写

```python

from mylib.ostk_lite import SubscriptableFileIO
with SubscriptableFileIO('filepath') as f:
    f[-10:] = b'123abc'
    print(f[123:456])
```

#### [Simple Telegram Bot](mylib/tg_bot.py#L35)

a very easy-to-use and write-less-do-more wrapper class of [PTB](https://github.com/python-telegram-bot/python-telegram-bot/ 'python-telegram-bot')

make a Telegram bot like this:

```python
from mylib.tg_bot import SimpleBot, deco_factory_bot_handler_method
from telegram.ext import CommandHandler
class MyBot(SimpleBot):
    @deco_factory_bot_handler_method(CommandHandler)
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

#### [PotPlayerKit](mylib/shards/potplayer.py)

toolkit for PotPlayer.
main features in current version:
- find opened PotPlayer window and bring it to foreground
- get and parse info of the opened media file
- rename/move the opened media file
- a [GUI dialog](mylib/gui_old.py#L44) to rename/move the opened media file

#### [VoidDuck](mylib/tricks.py#L141)

虚空之鸭，万能的鸭鸭，无能的鸭鸭，随你怎么对待它，鸭鸭不反抗，鸭鸭不回答

a void, versatile, useless and quiet duck, called anyhow, no return no raise

#### [PixivFanboxAPI](mylib/sites/pixiv.py#L71)

pixivFANBOX API (incomplete but usable)

- api
    - get_post_info
    - get_creator_info
    - list_post_of_creator
    - list_sponsor_plan_of_creator
- download
    - download_pixiv_fanbox_post
    - download_pixiv_fanbox_creator
