#!/usr/bin/env python

from bs4 import BeautifulSoup
import requests
import logging
import re as regex
import json
import zipfile
from multiprocessing.dummy import Pool
# import platform

from lib_misc import rectify_path_char
# if platform.system() == 'Linux':
#     from multiprocessing import Pool
# else:
#     from multiprocessing.dummy import Pool


def get_soup(uri: str, parser: str = 'lxml', retry: int = 3):
    """get_soup(uri) -> `bs4.BeautifulSoup` or `str` or `False`"""
    if '.' in uri.rsplit('/', maxsplit=1)[-1]:
        return uri
    if uri == '#':
        return False
    while retry:
        try:
            r = requests.get(uri)
            return BeautifulSoup(r.content, parser)
        except requests.exceptions.MissingSchema:
            return False
        finally:
            retry -= 1


class HentaiException(Exception):
    pass


class HentaiDownloadError(HentaiException):
    pass


class HentaiCafeKit:
    def __init__(self, max_dl: int = 5):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_dl = max_dl
        self.dl_pool = self.get_pool(max_dl)

    def parse(self, uri: str) -> list:
        logger = self.logger
        logger.info('<<< {}'.format(uri))
        soup = get_soup(uri)
        if soup(text='Read Online'):  # It's an entry, just get the chapters.
            yield from self.get_chapters(soup)
        else:  # It's not an entry, but a search-result-page.
            entries = [i['href'] for i in soup('a', class_='entry-thumb')]
            for entry_uri in entries:  # All chapters in all entries.
                logger.debug('<<<<< {}'.format(entry_uri))
                entry_soup = get_soup(entry_uri)
                yield from self.get_chapters(entry_soup)
            if not regex.search(r'/page/\d+/', uri) and soup.find('span', class_='current'):  # Traverse
                current = soup.find('span', class_='current').text
                try:
                    last = soup.find('a', class_='last', title='Last Page').text
                except AttributeError:
                    last = soup('a', class_='single_page')[-1].text
                single = soup.find('a', class_='single_page')['href']
                for n in list(range(int(current) + 1, int(last) + 1)):  # Traverse next page.
                    n_uri = regex.sub(r'/page/\d+', r'/page/{}'.format(n), single)  # URI of next page
                    logger.info('<<< {}'.format(n_uri))
                    n_soup = get_soup(n_uri)
                    n_entries = [i['href'] for i in n_soup('a', class_='entry-thumb')]  # entries on next page
                    for entry_uri in n_entries:  # Similar as above.
                        logger.debug('<<<<<< {}'.format(entry_uri))
                        entry_soup = get_soup(entry_uri)
                        yield from self.get_chapters(entry_soup)

    def get_chapters(self, entry_soup: BeautifulSoup) -> list:
        """get_chapters(entry_soup) -> [(ch1_uri, ch1_title), (ch2_uri, ch2_title), ...]"""
        logger = self.logger
        title = entry_soup.h3.decode_contents()
        logger.debug('Headline: {}'.format(title))
        info = entry_soup.find('div', class_='x-column x-sm x-1-2 last')('p')
        chapters = info[1:]
        if chapters:  # more than one chapter
            cover_uri = entry_soup.find('div', class_='entry-thumb').img['src']
            result_l = [(cover_uri, '{} - cover'.format(title))]
            for c in chapters:
                chapter_uri = c.a['href']
                chapter_title = c.strong.decode_contents()
                chapter_title = '{} {}'.format(
                    title,
                    regex.sub(
                        r'^Chapter (\d+): (.*)$',
                        r'ch.\1 - \2',
                        chapter_title,
                    )
                )
                result_l.append((chapter_uri, chapter_title))
            return result_l
        else:  # single chapter
            chapter_uri = info[0].find('a', title="Read")['href']
            chapter_title = title
            return [(chapter_uri, chapter_title)]

    def get_pages(self, chapter_uri: str) -> list or None:
        """get_pages(chapter_uri) -> [(image_uri, image_name), ...]"""
        logger = self.logger
        soup = get_soup(chapter_uri)
        if soup:
            if isinstance(soup, str):
                return [(soup, chapter_uri.rsplit('/', 1)[-1])]
            else:
                pages_l = json.loads(regex.search(r'var pages = (.*);', soup('script')[-1].decode()).group(1))
                logger.info(' └─ {} pages total.'.format(len(pages_l)))
                result_l = []
                for d in pages_l:
                    result_l.append((d['thumb_url'], d['filename']))
                return result_l
        else:
            return

    def get_pool(self, num: int):
        self.logger.info('====== {}x thread pool'.format(num))
        p = Pool(num)
        self.logger.debug(p)
        return p

    def set_pool(self, num: int = None):
        if num:
            self.dl_pool = self.get_pool(num)
        else:
            self.dl_pool = self.get_pool(self.max_dl)

    def download_page(self, uri: str, name: str, retry: int = 3):
        """download_page(uri, name, retry=3) -> (image: bytes, name: str, size: int) or `None`"""
        logger = self.logger
        get = requests.get
        while retry:
            r = get(uri)
            code = r.status_code
            reason = r.reason
            if r.ok:
                src_size = int(r.headers['Content-Length'])
                image = r.content
                dl_size = len(image)
                if dl_size == src_size:
                    logger.debug('[{}] {} {} ({}) {}'.format(code, name, reason, dl_size, uri))
                    return image, name, dl_size
                else:
                    logger.warning('[{}] {} {} ({}/{}) {}'.format(code, name, reason, dl_size, src_size, uri))
            else:
                logger.warning('[{}] {} {} {}'.format(code, name, reason, uri))
            retry -= 1
        else:
            logger.warning('Max retries reached for {} {}'.format(name, uri))
            raise HentaiDownloadError

    def download_page_wrap_tuple_args(self, pages: tuple):
        uri, name = pages
        return self.download_page(uri, name)

    def download_pages_gen(self, pages: list):
        yield from self.dl_pool.imap(self.download_page_wrap_tuple_args, pages)

    def download_chapter_gen(self, chapter_uri: str):
        """download_chapter_gen(chapter_uri) -> generator -> yield: (image: bytes, name: str, size: int)"""
        pages = self.get_pages(chapter_uri)
        if pages:
            return self.download_pages_gen(pages)
        else:
            return None

    def save_entry_to_cbz(self, uri: str):
        """Save a chapter to a local \".cbz\" file."""
        logger = self.logger
        chapters = self.parse(uri)
        for ch_uri, ch_title in chapters:
            logger.debug((ch_uri, ch_title))
            logger.info('{} ({})'.format(ch_title, ch_uri))
            chapter_dl = self.download_chapter_gen(ch_uri)
            if chapter_dl:
                with zipfile.ZipFile('{}.cbz'.format(rectify_path_char(ch_title)), 'w') as cbz:
                    logger.debug(cbz)
                    for image, name, size in chapter_dl:
                        logger.info('{}: {} ({})'.format(ch_title, name, size))
                        cbz.writestr(name, image)
                    cbz.close()
