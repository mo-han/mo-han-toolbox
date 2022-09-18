#!/usr/bin/env python3
import os
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

    @staticmethod
    def sxe_str2tuple(s: str):
        if not re.fullmatch(r'\d*x\d+'):
            raise TypeError('SxE string, e.g. 2x03, x01')
        s, e = ezdict.pick_to_list(re.MatchWrapper(re.match(r'(\d*)x(\d+)', s), [int]).all_groups(), )
        return s, e

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

    @displayepisode.setter
    def displayepisode(self, value):
        self.xml_etree.getroot().find('displayepisode').text = f'{value:d}'

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

    def make_se_patterns(self, more_se_pairs: list = None):
        se_pairs = more_se_pairs or []
        s = self.season
        e = self.episode
        ds = self.displayseason
        de = self.displayepisode
        if s >= 0 and e > 0:
            se_pairs.append((s, e))
        if ds >= 0 and de > 0:
            se_pairs.append((ds, de))
        elif de > 0 and s >= 0:
            se_pairs.append((s, de))
        return [f's{s}e{e:02d}' for s, e in sorted(set(se_pairs))]

    def _rename(self, old, new):
        if new == old:
            __logger__.debug(f'# {old}')
        else:
            with os.ctx_pushd(self.dirname):
                Config.dryrun or os.renames(old, new)
                __logger__.info(f'* {new} <- {old}')

    def rename_all(self, new_basename_maker, more_se_pairs=None):
        sidecar_files = self.get_sidecar_files_basename()
        patterns = self.make_se_patterns(more_se_pairs)
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
@ap.arg('season', type=int)
@ap.arg('episode', type=StrKit.to_range)
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
@ap.arg('SxE', nargs='*', type=KodiTvShowNfo.sxe_str2tuple)
@ap.opt('v', 'verbose', action='count', default=0)
@ap.true('D', 'dryrun')
@ap.map(method='method', verbose='verbose', dryrun='dryrun', more_se_pairs='SxE')
def sxe(method, verbose, dryrun, more_se_pairs):
    """handle SxE style episode numbering"""
    Config.dryrun = dryrun
    logging.init_root(logging.FMT_MESSAGE_ONLY)
    if verbose >= 2:
        logging.set_root_level('DEBUG')
    elif verbose:
        logging.set_root_level('INFO')
    m = getattr(KodiTvShowNfo, f'basename_maker_{method}_season_x_episode')
    for x in KodiTvShowNfo.map_instances(iter_path()):
        x.rename_all(m, more_se_pairs=more_se_pairs)


@ap.sub()
def nfo_bili_info():
    for nfo in KodiTvShowNfo.map_instances(iter_path()):
        nfo.title = re.split(r' \[bilibili', nfo.title)[0]
        info_fp = os.split_ext(nfo.filename)[0] + '.info'
        if os.path_isfile(info_fp):
            nfo.xml_etree.getroot().find('plot').text = io.IOKit.read_exit(open(info_fp, encoding='utf-8-sig'))
        nfo.save_nfo()
        if os.path_isfile(info_fp):
            os.remove(info_fp)


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
