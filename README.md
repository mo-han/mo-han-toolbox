---
typora-copy-images-to: _media
---

# Table of Contents
[TOC]

# etc

##Nginx Snippets

`etc/nginx`

Some useful snippets for Nginx configurations.

Feel free to copy / modify them or include them.

##My vimrc

`etc/vimrc`

# Downloaders

## Image Scrapers

### hentai_cafe.py

Download manga from *hentai.cafe*, and save as `.cbz` file.

***Python3 only***

Dependencies:

- requests
- bs4
- lxml


- `lib_hentai.py`
- `lib_misc.py`

```
Usage: hentai_cafe.py url
```

### photosmasters.py

Download all images under a album from photosmasters.com

***Python3 only***

*Single executable file, just download and use it.*

```
usage: photosmasters.py [-h] [-v] dir url

Album photos downloader for photosmasters.com

positional arguments:
  dir            download directory
  url            album URL of photosmasters.com

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose
```

