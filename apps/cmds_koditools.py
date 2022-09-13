#!/usr/bin/env python3
from xml.etree import ElementTree

from ezpykitext.appkit import *

__logger__ = logging.get_logger(__name__)
ap = argparse.ArgumentParserWrapper()

TV_SHOW_NFO_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!--created on  - tinyMediaManager 4.3.3-->
<episodedetails>
  <title></title>
  <originaltitle/>
  <showtitle></showtitle>
  <season>-1</season>
  <episode>-1</episode>
  <displayseason>-1</displayseason>
  <displayepisode>-1</displayepisode>
  <id/>
  <ratings/>
  <userrating>0.0</userrating>
  <plot></plot>
  <runtime>0</runtime>
  <mpaa/>
  <premiered/>
  <aired/>
  <watched>false</watched>
  <playcount>0</playcount>
  <trailer/>
  <dateadded></dateadded>
  <epbookmark/>
  <code/>
  <!--tinyMediaManager meta data-->
  <source>UNKNOWN</source>
  <original_filename></original_filename>
  <user_note/>
</episodedetails>
'''


class Config:
    dryrun = True

    @classmethod
    def is_dryrun(cls):
        return bool(cls.dryrun)


class KodiTvShowNfo:
    class InvalidNfoFile(Exception):
        pass

    def __init__(self, fp):
        if not os.path_isfile(fp):
            raise self.InvalidNfoFile('not a file', fp)
        dirname, stem, ext = os.split_path_dir_stem_ext(fp)
        if ext.lower() != '.nfo':
            raise self.InvalidNfoFile('not a .nfo file', fp)
        try:
            self.xml_etree = ElementTree.parse(fp)
        except ElementTree.ParseError:
            __logger__.error(f'! {fp}')
            raise
        self.dirname = dirname
        self.stem = stem
        self.ext = ext

    @property
    def basename(self):
        return self.stem + self.ext

    @property
    def filename(self):
        return os.join_path(self.dirname, self.basename)

    @property
    def episode(self):
        return int(self.xml_etree.getroot().find('episode').text)

    @episode.setter
    def episode(self, value):
        self.xml_etree.getroot().find('episode').text = f'{value:d}'

    @property
    def season(self):
        return int(self.xml_etree.getroot().find('season').text)

    @season.setter
    def season(self, value):
        self.xml_etree.getroot().find('season').text = f'{value:d}'

    @property
    def title(self):
        return self.xml_etree.getroot().find('title').text

    @title.setter
    def title(self, value):
        self.xml_etree.getroot().find('title').text = str(value)

    @property
    def displayepisode(self):
        return int(self.xml_etree.getroot().find('displayepisode').text)

    @property
    def displayseason(self):
        return int(self.xml_etree.getroot().find('displayseason').text)

    def save_nfo(self):
        self.xml_etree.write(self.filename, encoding='UTF-8', xml_declaration=True)

    def set_nfo(self, new_nfo_basename):
        with os.ctx_pushd(self.dirname):
            # self.xml = ElementTree.parse(nfo_basename).getroot()
            self.stem, self.ext = os.split_ext(new_nfo_basename)
        self.xml_etree = ElementTree.parse(self.filename)

    def _check_stem(self, fp):
        stem = os.split_path_dir_stem_ext(fp)[1]
        return stem == self.stem or stem.startswith(self.stem + '.') or stem.startswith(self.stem + '-')

    def get_sidecar_files_basename(self):
        with os.ctx_pushd(self.dirname):
            return [f for f in os.listdir() if self._check_stem(f) and f != self.basename]

    def get_all_season_x_episode_pattern(self):
        findall = self.xml_etree.getroot().findall
        return [f's{int(s.text):d}e{int(e.text):02d}' for s, e in itertools.chain(
            zip(findall('season'), findall('episode')),
            zip(findall('displayseason'), findall('displayepisode')),
        ) if '-1' not in (s.text, e.text)]

    def _rename(self, old, new):
        if new == old:
            __logger__.debug(f'# {old}')
        else:
            with os.ctx_pushd(self.dirname):
                Config.dryrun or os.renames(old, new)
                __logger__.info(f'* {new} <- {old}')

    def rename_all(self, new_basename_maker):
        sidecar_files = self.get_sidecar_files_basename()
        patterns = self.get_all_season_x_episode_pattern()
        for old in sidecar_files:
            new = new_basename_maker(old, patterns)
            self._rename(old, new)
        old_nfo = self.basename
        new_nfo = new_basename_maker(old_nfo, patterns)
        self._rename(old_nfo, new_nfo)
        self.set_nfo(new_nfo)

    @staticmethod
    def basename_maker_remove_season_x_episode(basename, patterns):
        new = basename
        for p in patterns:
            p_space = p + ' '
            if p_space in new:
                new = new.replace(p_space, '')
            for suffix in ('-', '.'):
                p_suffix = f' {p}{suffix}'
                if p_suffix in new:
                    new = new.replace(p_suffix, suffix)
        return new

    @classmethod
    def basename_maker_add_season_x_episode(cls, basename, patterns):
        removed = cls.basename_maker_remove_season_x_episode(basename, patterns)
        patterns_s = ' '.join(patterns)
        return f'{patterns_s} {removed}'

    @classmethod
    def basename_maker_update_season_x_episode(cls, basename, patterns):
        cleared = cls.basename_maker_clear_season_x_episode(basename)
        patterns_s = ' '.join(patterns)
        return f'{patterns_s} {cleared}'

    @staticmethod
    def basename_maker_clear_season_x_episode(basename, *args):
        return re.sub(r'(\d+x\d+\s?)|(\s?\d+x\d+)|(^(s\d+e\d+ )*)', '', basename)

    @classmethod
    def map_instances(cls, filepaths):
        r = []
        for fp in filepaths:
            with contextlib.suppress(cls.InvalidNfoFile):
                r.append(cls(fp))
        return r

    @classmethod
    def new(cls, nfo_fp, overwrite=False):
        if not overwrite and os.path_isfile(nfo_fp):
            __logger__.debug(f'# already existing NFO: {nfo_fp}')
            return cls(nfo_fp)
        io.IOKit.write_exit(open(nfo_fp, 'w', encoding='utf8'), TV_SHOW_NFO_TEMPLATE)
        o = cls(nfo_fp)
        root = o.xml_etree.getroot()
        root.find('plot').text = o.stem
        root.find('title').text = o.stem
        o.save_nfo()
        __logger__.debug(f'+ {o.filename}')
        return o

    def list_siblings(self):
        with os.ctx_pushd(self.dirname):
            season_episode_l = []
            for p in os.listdir():
                try:
                    nfo = self.__class__(p)
                except self.InvalidNfoFile:
                    continue
                for pair in [(nfo.season, nfo.episode), (nfo.displayseason, nfo.displayepisode)]:
                    if pair >= (1, 1):
                        season_episode_l.append(pair)
            return season_episode_l

    def enum_season_episode_appending(self, default_season: int, default_episode: int):
        siblings = self.list_siblings()
        if siblings:
            self.season, self.episode = max(siblings)
            self.episode += 1
        else:
            self.season, self.episode = default_season, default_episode
        self.save_nfo()
        return self.season, self.episode


@ap.sub()
@ap.opt('s', 'season', type=int, required=True)
@ap.opt('e', 'episode', type=StrKit.to_range, required=True)
@ap.map(season='season', episode_range='episode')
def nfo_sxe(season, episode_range: T.Iterator):
    """create kodi format tvshow nfo, setup season & episode, and rename all"""
    logging.init_root(logging.FMT_MESSAGE_ONLY)
    logging.set_root_level('DEBUG')
    Config.dryrun = False

    season_num = season
    last_episode_num = 0
    for p in iter_path():
        if not os.path_isfile(p):
            continue
        nfo_fp = os.split_ext(p)[0] + '.nfo'
        nfo = KodiTvShowNfo.new(nfo_fp)

        nfo.season = season_num
        try:
            episode_num = next(episode_range)
        except StopIteration:
            episode_num = last_episode_num + 1
        nfo.episode = episode_num
        nfo.save_nfo()
        last_episode_num = episode_num

        nfo.rename_all(KodiTvShowNfo.basename_maker_update_season_x_episode)


@ap.sub()
@ap.arg('method', choices=('add', 'remove', 'clear', 'update'))
@ap.opt('v', 'verbose', action='count', default=0)
@ap.true('D', 'dryrun')
@ap.map(method='method', verbose='verbose', dryrun='dryrun')
def sxe(method, verbose, dryrun):
    """handle SxE style episode numbering"""
    Config.dryrun = dryrun
    logging.init_root(logging.FMT_MESSAGE_ONLY)
    if verbose >= 2:
        logging.set_root_level('DEBUG')
    elif verbose:
        logging.set_root_level('INFO')
    m = getattr(KodiTvShowNfo, f'basename_maker_{method}_season_x_episode')
    for x in KodiTvShowNfo.map_instances(iter_path()):
        x.rename_all(m)


@ap.sub()
def nfo_bili_info():
    for nfo in KodiTvShowNfo.map_instances(iter_path()):
        nfo.title = re.split(r' \[bilibili', nfo.title)[0]
        info_fp = os.split_ext(nfo.filename)[0] + '.info'
        if os.path_isfile(info_fp):
            nfo.xml_etree.getroot().find('plot').text = io.IOKit.read_exit(open(info_fp, encoding='utf-8-sig'))
        nfo.save_nfo()


@ap.sub()
@ap.arg('season', type=int, help='default season number')
@ap.arg('episode', type=int, default=11, nargs='?', help='default episode number')
@ap.opt('v', 'verbose', action='count', default=0)
@ap.true('w', 'overwrite')
@ap.map(season='season', episode='episode', verbose='verbose', overwrite='overwrite')
def make_tvshow_nfo(season, episode, verbose, overwrite):
    """create nfo and set season & episode"""
    logging.init_root(logging.FMT_MESSAGE_ONLY)
    if verbose >= 2:
        logging.set_root_level('DEBUG')
    elif verbose:
        logging.set_root_level('INFO')
    nfo_fpl = [KodiTvShowNfo.new(os.split_ext(e)[0] + '.nfo', overwrite=overwrite).filename for e in iter_path()]
    for x in KodiTvShowNfo.map_instances(nfo_fpl):
        if (x.season, x.episode) >= (1, 1):
            __logger__.info(f'# season & episode set already: {x.filename}')
            continue
        x.enum_season_episode_appending(season, episode)
        __logger__.info(f'* {x.season}x{x.episode}: {x.filename}')


def main():
    ap.parse()
    ap.run()


if __name__ == '__main__':
    main()
