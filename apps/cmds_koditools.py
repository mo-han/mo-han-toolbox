#!/usr/bin/env python3
from xml.etree import ElementTree

from ezpykitext.appkit import *

__logger__ = logging.get_logger(__name__)
ap = argparse.ArgumentParserWrapper()


class Config:
    dryrun = True

    @classmethod
    def is_dryrun(cls):
        return bool(cls.dryrun)


class KodiNfo:
    class InvalidNfoFile(Exception):
        pass

    def __init__(self, fp):
        if not os.path_isfile(fp):
            raise self.InvalidNfoFile('not a file', fp)
        dirname, stem, ext = os.split_path_dir_stem_ext(fp)
        if ext.lower() != '.nfo':
            raise self.InvalidNfoFile('not a .nfo file', fp)
        self.xml = ElementTree.parse(fp).getroot()
        self.dirname = dirname
        self.stem = stem
        self.ext = ext

    @property
    def nfo_basename(self):
        return self.stem + self.ext

    def update_nfo(self, new_nfo_basename):
        with os.ctx_pushd(self.dirname):
            # self.xml = ElementTree.parse(nfo_basename).getroot()
            self.stem, self.ext = os.split_ext(new_nfo_basename)

    def _check_stem(self, fp):
        stem = os.split_path_dir_stem_ext(fp)[1]
        return stem == self.stem or stem.startswith(self.stem + '.') or stem.startswith(self.stem + '-')

    def get_sidecar_files_basename(self):
        with os.ctx_pushd(self.dirname):
            return [f for f in os.listdir() if self._check_stem(f) and f != self.nfo_basename]

    def get_all_season_x_episode_pattern(self):
        findall = self.xml.findall
        return [f'{int(s.text):d}x{int(e.text):02d}' for s, e in itertools.chain(
            zip(findall('season'), findall('episode')),
            zip(findall('displayseason'), findall('displayepisode')),
        )]

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
        old_nfo = self.nfo_basename
        new_nfo = new_basename_maker(old_nfo, patterns)
        self._rename(old_nfo, new_nfo)
        self.update_nfo(new_nfo)

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
        cleared = cls.basename_maker_remove_season_x_episode(basename, patterns)
        patterns_s = ' '.join(patterns)
        return f'{patterns_s} {cleared}'

    @staticmethod
    def basename_maker_clear_season_x_episode(basename, *args):
        return re.sub(r'(\d+x\d+[\s]?)|([\s]?\d+x\d+)', '', basename)

    @classmethod
    def map_instances(cls, filepaths):
        r = []
        for fp in filepaths:
            with contextlib.suppress(cls.InvalidNfoFile):
                r.append(cls(fp))
        return r


@ap.sub()
@ap.arg('method', choices=('add', 'remove', 'clear',))
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
    m = getattr(KodiNfo, f'basename_maker_{method}_season_x_episode')
    for x in KodiNfo.map_instances(iter_path()):
        x.rename_all(m)


def main():
    ap.parse()
    ap.run()


if __name__ == '__main__':
    main()
