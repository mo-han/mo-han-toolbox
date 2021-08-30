
Table of Contents
=================

* [Wrapper](#wrapper)
* [AttrName](#attrname)
* [ArgumentParserRigger](#argumentparserrigger)
* [SubscriptableFileIO](#subscriptablefileio)
* [Simple Telegram Bot](#simple-telegram-bot)
* [bilibili\_aocx](#bilibili_aocx)
* [mykit\.py](#mykitpy)
  * [wrap\.ffmpeg (aliases: ffmpeg, ff)](#wrapffmpeg-aliases-ffmpeg-ff)
  * [wrap\.ffprobe (aliases: ffprobe, ff)](#wrapffprobe-aliases-ffprobe-ff)
* [DownloadPool](#downloadpool)
* [PotPlayerKit](#potplayerkit)
* [VoidDuck](#voidduck)
* [PixivFanboxAPI](#pixivfanboxapi)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc.go)


#### Wrapper

[mylib/wrapper](https://github.com/mo-han/mo-han-toolbox/tree/master/mylib/wrapper)

- cwebp
- tesseract-ocr


#### AttrName

its attribute is a str same as the name thereof

实例的属性总是一个和属性名称相同的字符串

```python
from mylib.easy import AttrName

an = AttrName()
assert an.abc_xyz == 'abc_xyz'
an.abc_xyz = 123456  # nothing happens
```

#### ArgumentParserRigger

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

from mylib.easy.argparse import *

apr = ArgumentParserRigger()
an = apr.an  # an.abc_xyz == 'abc_xyz'
an.x = an.y = an.z = an.l = ''  # let the IDE remember these attr names


@apr.sub(lambda x: x.replace('_', '-'))  # xyz_and_more -> xyz-and-more
@apr.arg(an.x)
@apr.arg(an.y)
@apr.arg(an.z)
# flag means option with action='store_true', so the flag 'l' means option '-l'
@apr.flag(an.l, help='print in multiple lines')
# arg x -> param x, int(1111) -> param y, arg z -> param z, unknown_args -> param y, flag -l -> param multi_line
@apr.map(an.x, apr.ro(1111), an.z, apr.skip, multi_line=an.l)
def xyz_and_more(x, y, z, more, multi_line=False):
  print(f'x={x}', f'y={y}', f'z={z}', f'and more: {", ".join(more)}', sep='\n' if multi_line else ', ')


@apr.sub()
@apr.arg('a')
@apr.arg('b')
@apr.map('a', 'b')
def ab(a, b):
  print(a, b)


apr.parse(catch_unknown_args=True)
apr.run()
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

#### SubscriptableFileIO

read/write file with slice

切片式文件读写

```python


from mylib.easy.io import SubscriptableFileIO
with SubscriptableFileIO('filepath') as f:
    f[-10:] = b'123abc'
    print(f[123:456])
```

#### Simple Telegram Bot

a very easy-to-use and write-less-do-more wrapper class of [PTB](https://github.com/python-telegram-bot/python-telegram-bot/ 'python-telegram-bot')

make a Telegram bot like this:

```python
from mylib.tg_bot import EasyBot, deco_factory_bot_handler_method
from telegram.ext import CommandHandler


class MyBot(EasyBot):
    @deco_factory_bot_handler_method(CommandHandler)
    def hello(self, update, context):
        """say hi"""
        self.__send_typing__(update)
        update.message.reply_text('Hi!')


bot = MyBot('TOKEN', auto_run=False)
bot.__run__()
```

#### bilibili_aocx

bilibili APP offline cache extractor

B站 移动端应用 离线缓存 提取器

bilibili mobile client APP offline cache extractor

[.exe pre-release](https://github.com/mo-han/mo-han-toolbox/releases/download/t0/bilibili_aocx.exe)

#### mykit.py

self-using multifunctional script

自用多功能脚本

some of the functions (sub commands):

##### wrap.ffmpeg (aliases: ffmpeg, ff)

a ffmpeg wrapper, can get source file(s) from clipboard

`mykit ff -k smallhd` equivalent to `ffmpeg -pix_fmt yuv420 -c:v hevc -crf 25` and scale down resolution into HD (1280x720)

##### wrap.ffprobe (aliases: ffprobe, ff)

a ffprobe wrapper, can get source file(s) from clipboard

`mykit fp` will print info of filepath in clipboard

#### DownloadPool

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

#### PotPlayerKit

toolkit for PotPlayer.
main features in current version:
- find opened PotPlayer window and bring it to foreground
- get and parse info of the opened media file
- rename/move the opened media file
- a GUI dialog to rename/move the opened media file

#### VoidDuck

虚空之鸭，万能的鸭鸭，无能的鸭鸭，随你怎么对待它，鸭鸭不反抗，鸭鸭不回答

a void, versatile, useless and quiet duck, called anyhow, no return no raise

#### PixivFanboxAPI

pixivFANBOX API (incomplete but usable)

- api
    - get_post_info
    - get_creator_info
    - list_post_of_creator
    - list_sponsor_plan_of_creator
- download
    - download_pixiv_fanbox_post
    - download_pixiv_fanbox_creator
