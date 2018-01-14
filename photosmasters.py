#!/usr/bin/env python3

from urllib.parse import urlparse, parse_qsl
from time import sleep
from threading import Thread
import re
import logging
import sys
import os
import argparse
import json

from requests import get, head
from bs4 import BeautifulSoup

from lib_misc import win32_ctrl_c, ExitCode, rectify_path_char, LOG_FMT, LOG_FMT_MESSAGE_ONLY

DB_FILE = 'db.json'
INFO_FILE = 'info.txt'

__program__ = 'photosmasters'
__description__ = 'Album photos downloader for photosmasters.com'
_logger = logging.getLogger('photosmasters')

db = {}
stat = {}
server = ''
thl = []


def parse_args():
    ap = argparse.ArgumentParser(description=__description__)
    ap.add_argument('dir', help='download directory')
    ap.add_argument('url', help='album URL of photosmasters.com')
    ap.add_argument('--threads', '-t', type=int, default=5, help='number of download threads')
    ap.add_argument('-v', '--verbose', action='store_true', )
    return ap.parse_args()


def restore_db(file: str):
    global db
    if os.path.exists(file):
        with open(file, 'r') as f:
            db = json.load(f)
        _logger.info('Restore database from {}'.format(file))


def save_db(file: str):
    with open(file, 'w') as f:
        json.dump(db, f)
    _logger.info('Save database to {}'.format(file))


def save_info(file: str):
    with open(file, 'w') as f:
        f.write('{}\n{}\n{}\n{}'.format(stat['at'], stat['ti'], db['name'], db['url']))
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


def image_from_photo(pid: str, purl: str, pdb: dict):
    global server
    if pdb:
        img_url = pdb['url']
    else:
        photo_soup, _ = soup(purl)
        img = photo_soup.img
        img_url = server + '/' + img['src']
        img_ext = os.path.splitext(img_url)[-1]
        img_alt = img['alt']
        img_size = None
        pdb = {'url': img_url, 'ext': img_ext, 'alt': img_alt, 'size': img_size, }
        db[pid] = pdb
    _logger.debug('Image: {}'.format(img_url))


def download(pid: str, purl: str, name: str):
    global server
    dl_dir = stat['dd']
    pdb = db.get(pid)
    image_from_photo(pid, purl, pdb)
    pdb = db[pid]
    pdb['name'] = name = rectify_path_char(name)
    url = pdb['url']
    file = os.path.join(dl_dir, '{} - {}{}'.format(name, pid, pdb['ext']))
    _logger.debug('{} <-> {}'.format(pdb, file))
    while True:
        try:
            if os.path.exists(file):
                local_size = os.stat(file).st_size
                pdb_remote_size = pdb['size']
                if pdb_remote_size:
                    remote_size = pdb_remote_size
                else:
                    remote_size = content_length(head(url))
                    pdb['size'] = remote_size
                if local_size == remote_size:
                    _logger.info('Good: {}'.format(file))
                    break
                else:
                    _logger.warning('Bad: {}'.format(file))
            r = get(url)
            if r.status_code == 200:
                with open(file, 'wb') as f:
                    f.write(r.content)
                pdb['size'] = content_length(r)
                _logger.info('OK: {} -> {}'.format(url, file))
                break
            else:
                _logger.warning('Fail: {}'.format(url))
        except Exception:
            raise


def url_split(url: str):
    host = re.sub(r'^(.*://.*?)/.*', r'\1', url)
    path = re.sub(r'^.*://.*?(/.*$)', r'\1', url)
    if path == host:
        path = ''
    return host, path


def get_query_dict(url: str):
    query = urlparse(url)[4]
    return dict(parse_qsl(query))


def display_stat():
    _logger.info('[{li}/{ti}][{lp}/{tp}] {at} -->> {dd}'.format(**stat))


def main(url: str = None):
    win32_ctrl_c()
    args = parse_args()
    # Get verbose level from args
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
    # Get URL from args
    if url:
        album_url = url
    else:
        album_url = args.url
        if re.search(r'photosmasters\.com/thumbnails\.php\?album=', album_url):
            album_url = re.sub(r'(^.*?album=\d*).*$', r'\1', album_url)
        else:
            _logger.warning('NOT A PHOTOSMASTERS.COM URL!')
            sys.exit()
        db['url'] = album_url
    global server
    server, _ = url_split(album_url)
    # Parse album page
    album_soup, _ = soup(album_url)
    if album_soup('div', class_='cpg_message_warning'):
        _logger.warning('ALBUM NOT EXISTS!')
        sys.exit()
    album_title = album_soup.title.contents[0]
    album_name = re.sub(r'^(.*) - photosmasters\.com', r'\1', album_title)
    album_name = re.sub(r'^.* \((.*)\)', r'\1', album_name)
    album_name = album_name.strip()
    db['name'] = album_name
    _logger.info(album_title)
    # Get album directory to store downloaded photos
    album_id = get_query_dict(album_url)['album']
    album_dir = os.path.join(args.dir, 'photosmasters', album_name)
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)
    _logger.info('{} -->> {}'.format(album_url, album_dir))
    # Meta
    info_file = os.path.join(album_dir, INFO_FILE)
    db_file = os.path.join(album_dir, DB_FILE)
    restore_db(db_file)
    totals = album_soup('td', class_='tableh1')[0].contents[0]
    _, total_images, _, _, total_pages = totals.split()
    global stat
    stat = {
        'dd': album_dir,  # download directory
        'at': album_title,  # title
        'ti': int(total_images),  # total images
        'tp': int(total_pages),  # total pages
        'li': 0,  # last image
        'lp': 0,  # last page
    }
    display_stat()
    # Let's roll out
    try:
        for _ in range(stat['tp']):
            stat['lp'] += 1
            page_url = '{}&page={}'.format(album_url, stat['lp'])
            _logger.debug('Page: {}'.format(page_url))
            page_soup, _ = soup(page_url)
            thumbnails = page_soup('td', class_='thumbnails')
            for thumb in thumbnails:
                if not thumb.td:
                    break
                stat['li'] += 1
                thumb_title = thumb.td.span.contents[0]
                photo_url = server + '/' + thumb.a['href'].replace('#top_display_media', '&fullsize=1')
                _logger.debug('Photo: {}'.format(photo_url))
                photo_id = get_query_dict(photo_url)['pid']
                # Go!
                th = Thread(target=download, args=(photo_id, photo_url, thumb_title))
                while len(thl) >= args.threads:
                    for t in thl:
                        if not t.is_alive():
                            thl.remove(t)
                    sleep(0.1)
                display_stat()
                th.start()
                thl.append(th)
                sleep(0.1)
    except KeyboardInterrupt:
        _logger.info('Wait: {} threads to finish.'.format(len(thl)))
        sys.exit(ExitCode.CTRL_C)
    finally:
        for th in thl:
            th.join()
        save_db(db_file)
        save_info(info_file)


if __name__ == '__main__':
    main()
