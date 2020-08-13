#### [SubscriptableFileIO](mylib/os_util.py#L225)

slice data in FileIO object

```python
from mylib.os_util import SubscriptableFileIO

with SubscriptableFileIO('filepath') as f:
    f[-10:] = b'123abc'
```

#### [bilibili_aocx](mykits/bilibili_aocx.py)

*bilibili APP offline cache extractor*

B站 移动端应用 离线缓存 提取器

bilibili mobile client APP offline cache extractor

[.exe pre-release](https://github.com/mo-han/mo-han-toolbox/releases/download/t0/bilibili_aocx.exe)

#### [PotPlayerKit](mylib/potplayer.py)

toolkit for PotPlayer.
main features in current version:
- find opened PotPlayer window and bring it to foreground
- get and parse info of the opened media file
- rename/move the opened media file
- a [GUI dialog](mylib/gui.py#L44) to rename/move the opened media file

#### [VoidDuck](mylib/tricks.py#L135)

虚空之鸭，万能的鸭鸭，无能的鸭鸭，随你怎么对待它，鸭鸭不反抗，鸭鸭不回答

a void, versatile, useless and quiet duck, called anyhow, no return no raise