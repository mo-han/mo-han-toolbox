#!/usr/bin/env python

from re import sub
from urllib.parse import urlparse, parse_qsl
import logging
from time import sleep
import sys
import os
import argparse
import json

from requests import get, head
from bs4 import BeautifulSoup

from lib_misc import ExitCode, LOG_FMT, LOG_FMT_MESSAGE_ONLY

DB_FILE = 'db.json'
INFO_FILE = 'info.txt'

__program__ = 'photosmasters'
__description__ = 'Crawler of photosmasters.com'
_logger = logging.getLogger('photosmasters')


def parse_args():
    ap = argparse.ArgumentParser(description=__description__)
    ap.add_argument('dir', help='download directory')
    ap.add_argument('url', help='album URL of photosmasters.com')
    ap.add_argument('-v', '--verbose', action='store_true',)
    return ap.parse_args()


def restore_db(db: dict, file: str):
    if os.path.exists(file):
        with open(file, 'r') as f:
            db = json.load(f)
        _logger.info('Restore database from {}'.format(file))


def save_db(db: dict, file: str):
    with open(file, 'w') as f:
        json.dump(db, f)
    _logger.info('Save database to {}'.format(file))


def save_info(stat: dict, file: str):
    with open(file, 'w') as f:
        f.write(stat['at'])
    _logger.info('Save info to {}'.format(file))


def soup(url: str) -> tuple:
    while True:
        try:
            r = get(url)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'lxml')
                h = r.headers
                return s, h
            else:
                _logger.warning('Retry: {}'.format(url))
        except Exception as e:
            _logger.error(repr(e))


def content_length(respond):
    return int(respond.headers['Content-Length'])


def download(pid: str, file: str, db: dict):
    while True:
        try:
            pdb = db[pid]
            url = pdb['src']
            if os.path.exists(file):
                local_size = os.stat(file).st_size
                pdb_remote_size = pdb['size']
                if pdb_remote_size:
                    if local_size == pdb_remote_size:
                        _logger.info('Finish: {}'.format(file))
                        break
                else:
                    remote_size = content_length(head(url))
                    if remote_size == local_size:
                        pdb['size'] = remote_size
                        _logger.info('Finish: {}'.format(file))
                        break
            else:
                r = get(url)
                if r.status_code == 200:
                    with open(file, 'wb') as f:
                        f.write(r.content)
                    pdb['size'] = content_length(r)
                    _logger.info('Download: {} -> {}'.format(url, file))
                    break
                else:
                    _logger.warning('Retry: {}'.format(url))
        except Exception as e:
            _logger.error(repr(e))


def url_split(url: str):
    server = sub(r'^(.*://.*?)/.*', r'\1', url)
    path = sub(r'^.*://.*?(/.*$)', r'\1', url)
    if path == server:
        path = ''
    return server, path


def get_query_dict(url: str):
    query = urlparse(url)[4]
    return dict(parse_qsl(query))


def display_stat(stat: dict):
    _logger.info('[{li}/{ti}][{lp}/{tp}] {at}'.format(**stat))


def gn_pages_per_album(url: str, stat: dict):
    album_soup, _ = soup(url)

    album_title = album_soup.title.contents[0]
    _logger.info(album_title)
    _logger.info(url)

    totals = album_soup('td', class_='tableh1')[0].contents[0]
    _, total_images, _, _, total_pages = totals.split()
    stat.update({
        'at': album_title,  # title
        'ti': int(total_images),  # total images
        'tp': int(total_pages),  # total pages
        'li': 0,  # last image
        'lp': 0,  # last page
    })
    display_stat(stat)

    for page in range(stat['tp']):
        stat['lp'] += 1
        page_url = '{}&page={}'.format(url, stat['lp'])
        _logger.debug('Page: {}'.format(page_url))
        yield page_url


def gn_photos_per_page(url: str, stat: dict, db: dict):
    server, _ = url_split(url)
    page_soup, _ = soup(url)
    for thumbnail in page_soup('td', class_='thumbnails'):
        stat['li'] += 1
        photo_url = server + '/' + thumbnail.a['href'].replace('#top_display_media', '&fullsize=1')
        _logger.debug('Photo: {}'.format(photo_url))
        photo_id = get_query_dict(photo_url)['pid']
        photo_soup, _ = soup(photo_url)
        photo_db = db.get(photo_id)
        if photo_db:
            img_src = photo_db.get('src')
        else:
            img = photo_soup.img
            img_src = server + '/' + img['src']
            img_alt = img['alt']
            img_size = None
            photo_db = {'src': img_src, 'alt': img_alt, 'size': img_size}
            db[photo_id] = photo_db
        _logger.debug('Image: {}'.format(img_src))
        yield photo_id


def main(url: str=None):
    args = parse_args()

    if args.verbose:
        lvl = logging.DEBUG
        fmt = LOG_FMT
    else:
        lvl = logging.INFO
        fmt = LOG_FMT_MESSAGE_ONLY
    logging.basicConfig(
        stream=sys.stderr,
        level=lvl,
        format=fmt,
    )

    if url:
        album_url = url
    else:
        album_url = args.url

    album_id = get_query_dict(album_url)['album']
    album_dir = os.path.join(args.dir, 'photosmasters', album_id)
    info_file = os.path.join(album_dir, INFO_FILE)
    db_file = os.path.join(album_dir, DB_FILE)
    stat = {}
    db = {}

    try:
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        restore_db(db, db_file)
        _logger.info('Directory: {}'.format(album_dir))

        for page_url in gn_pages_per_album(album_url, stat):
            for photo_id in gn_photos_per_page(page_url, stat, db):
                pdb = db[photo_id]
                file_name = '{}-{}'.format(photo_id, pdb['alt'])
                file_path = os.path.join(album_dir, file_name)
                display_stat(stat)
                download(photo_id, file_path, db)

    except KeyboardInterrupt:
        sys.exit(ExitCode.CTRL_C)
    finally:
        save_db(db, db_file)
        save_info(stat, info_file)


if __name__ == '__main__':
    main()
