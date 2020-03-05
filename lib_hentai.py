#!/usr/bin/env python
import datetime
import os
import requests
import logging
import re as regex
import json
import zipfile
from bs4 import BeautifulSoup
from time import sleep
from multiprocessing.dummy import Pool
# import platform

from lib_base import rectify_basename

DRAW_LINE_LENGTH = 32

_requests_session = requests.Session()
_requests_session.headers['User-Agent'] = \
    'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) ' \
    'AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'


class HentaiException(Exception):
    pass


class HentaiRequestError(HentaiException):
    pass


class HentaiParseError(HentaiException):
    pass


class HentaiDownloadError(HentaiException):
    pass


def get_lxml_soup(r: requests.Response, *args, **kwargs):
    return BeautifulSoup(r.content, 'lxml', *args, **kwargs)


def http_get(url: str, head_only: bool = False, max_retries: int = 3, retry_interval: float = 5.0, ):
    """Wrapper of requests.get, with some extra param."""
    if head_only:
        req = _requests_session.head
    else:
        req = _requests_session.get
    error_args = ()
    while max_retries > 0:
        try:
            r = req(url)
            if r.ok:
                return r
            else:
                raise HentaiRequestError('Bad response.', url, r.status_code, r.reason)
        except requests.RequestException as e:
            error_args = e.args + error_args
            max_retries -= 1
            sleep(retry_interval)
    else:
        raise HentaiRequestError('Connection failed, out of retries.', url, *error_args)
    pass


class NHentaiKit:
    def __init__(self, max_dl: int = 3):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__max_dl = max_dl
        self.logger.info('{} downloading threads.'.format(self.__max_dl))
        self.__dl_pool = Pool(self.__max_dl)

    @property
    def dl_pool(self):
        return self.__dl_pool

    def get_gallery(self, url: str):
        self.logger.info(url)
        soup = get_lxml_soup(http_get(url))
        info = soup.find('div', id='info')
        h1 = info.h1.text
        self.logger.info(h1)
        try:
            h2 = info.h2.text
            self.logger.info(h2)
        except Exception as e:
            self.logger.warning(str(e))
        # src_id = soup.find('div', id='cover').img['data-src'].rsplit('/', 2)[-2]
        # gallery_path = url.split('://')[0] + '://i.nhentai.net/galleries/' + src_id
        # page_num = int(soup.find('div', id='info')('div')[-3].text.split(' pages')[0])
        # self.__logger.info('{} pages in {}'.format(page_num, gallery_path))
        all_thumb_url_l = [i.img['data-src'] for i in soup('a', class_='gallerythumb')]
        all_pic_url_l = [regex.sub(r'(.*)t.nhentai.net(.*)t.(.*)', r'\1i.nhentai.net\2.\3', s) for s in all_thumb_url_l]
        return h1, all_pic_url_l

    def download_picture(self, picture_url: str):
        try:
            p_name = picture_url.rsplit('/', 1)[-1]
            p_get = http_get(picture_url)
            p_src_size = int(p_get.headers['Content-Length'])
            p_data = p_get.content
            p_dl_size = len(p_data)
            self.logger.info('{} ({}/{}) {}'.format(p_name, p_dl_size, p_src_size, picture_url))
            if p_dl_size == p_src_size:
                return p_name, p_data
            else:
                raise HentaiDownloadError('Incomplete data', picture_url, p_src_size, p_dl_size)
        except HentaiRequestError as e:
            raise HentaiDownloadError(*e.args)

    def save_gallery_to_cbz(self, gallery_src: tuple, dl_dir: str = ''):
        if dl_dir:
            self.logger.info('Download to dir: {}'.format(dl_dir))
        title, all_pic_url_list = gallery_src
        cbz_name = rectify_basename(title) + '.cbz'
        self.logger.info('Save to file: {}'.format(cbz_name))
        cbz_path = os.path.join(dl_dir, cbz_name)
        err_log_path = cbz_path + '.error.log'
        with zipfile.ZipFile(cbz_path, 'w') as cbz:
            self.logger.debug(cbz)
            for pic_name, pic_data in self.dl_pool.imap_unordered(self.download_picture, all_pic_url_list):
                try:
                    cbz.writestr(pic_name, pic_data)
                except HentaiDownloadError as e:
                    with open(err_log_path, 'a') as error_log:
                        error_log.write(str(e))
                        error_log.write('\n')
                        error_log.close()
            cbz.close()


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
            # return False
            uri = 'http://' + uri
            retry += 1
        except requests.exceptions.InvalidSchema:
            uri = uri.split('://', maxsplit=1)
            uri = 'http://' + uri[1]
            retry += 1
        finally:
            retry -= 1


class HentaiException(Exception):
    pass


class HentaiParseError(HentaiException):
    pass


class HentaiDownloadError(HentaiException):
    pass


class HentaiCafeKit:
    __page_sum = ...  # type: int

    def __init__(self, max_dl: int = 3):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_dl = max_dl
        self.dl_pool = self.get_pool(max_dl)

    def save_entry_to_cbz(self, uri: str):
        """Save a chapter to a local \".cbz\" file."""
        logger = self.logger
        chapters = self.parse(uri)
        for ch_uri, ch_title in chapters:
            logger.info('-' * DRAW_LINE_LENGTH + '\n' + '{} ({})'.format(ch_title, ch_uri))
            try:
                chapter_dl = self.download_chapter_gen(ch_uri)
                dl_counter = 0
                print('Pages: [{}/{}]'.format(dl_counter, self.__page_sum), end='\r')
                if chapter_dl:
                    dl_file = 'dl.txt'
                    complete = False
                    try:
                        with zipfile.ZipFile('{}.cbz'.format(rectify_basename(ch_title)), 'r') as cbz:
                            if dl_file in cbz.namelist():
                                complete = True
                            cbz.close()
                    except (zipfile.BadZipFile, FileNotFoundError):
                        pass
                    if complete:
                        logger.info('(skip already downloaded)')
                    else:
                        with zipfile.ZipFile('{}.cbz'.format(rectify_basename(ch_title)), 'w') as cbz:
                            for image, name, size in chapter_dl:
                                dl_counter += 1
                                logger.debug('{}: {} ({})'.format(ch_title, name, size))
                                print('Pages: [{}/{}] ({}x)'.format(dl_counter, self.__page_sum, self.max_dl), end='\r')
                                cbz.writestr(name, image)
                            cbz.writestr(dl_file, datetime.datetime.utcnow().replace(
                                tzinfo=datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat())
                            cbz.close()
                        print()
                else:
                    print('(skip empty)')
            except HentaiParseError:
                logger.warning('ERROR WHEN PARSING THE MANGA!')

    def parse(self, uri: str) -> list:
        logger = self.logger
        logger.info('=' * DRAW_LINE_LENGTH + '\n' + '{}'.format(uri))
        soup = get_soup(uri)
        if soup(text='Read Online'):  # It's an entry, just get the chapters.
            yield from self.get_chapters(soup, uri)
        else:  # It's not an entry, but a search-result-page.
            entries = [i['href'] for i in soup('a', class_='entry-thumb')]
            for entry_uri in entries:  # All chapters in all entries.
                logger.debug('{}'.format(entry_uri))
                entry_soup = get_soup(entry_uri)
                yield from self.get_chapters(entry_soup, entry_uri)
            if not regex.search(r'/page/\d+/', uri) and soup.find('span', class_='current'):  # Traverse
                current = soup.find('span', class_='current').text
                try:
                    last = soup.find('a', class_='last', title='Last Page').text
                except AttributeError:
                    last = soup('a', class_='single_page')[-1].text
                single = soup.find('a', class_='single_page')['href']
                for n in list(range(int(current) + 1, int(last) + 1)):  # Traverse next page.
                    n_uri = regex.sub(r'/page/\d+', r'/page/{}'.format(n), single)  # URI of next page
                    logger.info('=' * DRAW_LINE_LENGTH + '\n' + '{}'.format(n_uri))
                    n_soup = get_soup(n_uri)
                    n_entries = [i['href'] for i in n_soup('a', class_='entry-thumb')]  # entries on next page
                    for entry_uri in n_entries:  # Similar as above.
                        logger.debug('{}'.format(entry_uri))
                        entry_soup = get_soup(entry_uri)
                        yield from self.get_chapters(entry_soup, entry_uri)

    def get_chapters(self, entry_soup: BeautifulSoup, entry_uri: str) -> list:
        """get_chapters(entry_soup) -> [(ch1_uri, ch1_title), (ch2_uri, ch2_title), ...]"""
        hc_id = entry_uri.split('/hc.fyi/')[-1]
        if not hc_id:
            hc_id = entry_uri.split('/')[-1]
        logger = self.logger
        title = entry_soup.h3.decode_contents()
        logger.debug('Headline: {}'.format(title))
        info = entry_soup.find('div', class_='x-column x-sm x-1-2 last')('p')
        chapters = info[1:]
        if chapters:  # more than one chapter
            cover_uri = entry_soup.find('div', class_='entry-thumb').img['src']
            result_l = [(cover_uri, '{} - cover'.format(title))]
            for c in chapters:
                chapter_uri = c.a['href'].split('<br')[0]
                chapter_title = c.strong.decode_contents()
                chapter_title = '{} {}'.format(
                    title,
                    regex.sub(
                        r'^Chapter (\d+): (.*)$',
                        r'ch.\1 - \2',
                        chapter_title,
                    )
                )
                chapter_title = '{} [hentai.cafe.{}]'.format(chapter_title, hc_id)
                chapter_title = chapter_title.replace('&amp;', '&')
                result_l.append((chapter_uri, chapter_title))
            return result_l
        else:  # single chapter
            chapter_uri = info[0].find('a', title="Read")['href'].split('<br')[0]
            chapter_title = '{} [hentai.cafe.{}]'.format(title, hc_id)
            chapter_title = chapter_title.replace('&amp;', '&')
            return [(   chapter_uri, chapter_title)]

    def get_pages(self, chapter_uri: str) -> list or None:
        """get_pages(chapter_uri) -> [(image_uri, image_name), ...]"""
        logger = self.logger
        soup = get_soup(chapter_uri)
        if soup:
            if isinstance(soup, str):
                return [(soup, chapter_uri.rsplit('/', 1)[-1])]
            else:
                # pages_l = json.loads(regex.search(r'var pages = (.*);', soup('script')[-2].decode()).group(1))
                for s in soup('script'):
                    r = regex.search(r'var pages = (.*);', s.decode())
                    if r:
                        pages_l = json.loads(r.group(1))
                        break
                else:
                    raise HentaiParseError
                self.__page_sum = len(pages_l)
                result_l = []
                for d in pages_l:
                    result_l.append((d['thumb_url'], d['filename']))
                return result_l
        else:
            return

    def get_pool(self, num: int):
        self.logger.debug('{}x thread pool'.format(num))
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
        # yield from self.dl_pool.imap(self.download_page_wrap_tuple_args, pages)
        yield from self.dl_pool.imap_unordered(self.download_page_wrap_tuple_args, pages)

    def download_chapter_gen(self, chapter_uri: str):
        """download_chapter_gen(chapter_uri) -> generator -> yield: (image: bytes, name: str, size: int)"""
        pages = self.get_pages(chapter_uri)
        if pages:
            return self.download_pages_gen(pages)
        else:
            return None
