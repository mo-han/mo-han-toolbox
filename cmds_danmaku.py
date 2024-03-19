#!/usr/bin/env python3
from xml.etree import ElementTree

from oldezpykitext.appkit import *

__logger__ = logging.get_logger(__name__)
ap = argparse.ArgumentParserWrapper()


def sign(x):
    if x == '+':
        return 1
    if x == '-':
        return -1
    raise ValueError(x)


def parse_time_offset(x):
    if isinstance(x, (float, int)):
        return x
    elif isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            d = re.BatchMatchWrapper(
                re.search(r'(?P<sign>[+-])?(?P<h>\d+):(?P<m>\d{1,2}):(?P<s>\d{1,2}(\.\d+)?)', x),
                re.search(r'(?P<sign>[+-])?(?P<m>\d+):(?P<s>\d{1,2}(\.\d+)?)', x),
                types=(sign, float,)
            ).first_match().pick_existing(h=0, m=0, s=0, sign=1)
            __logger__.debug(d)
            return (d['h'] * 3600 + d['m'] * 60 + d['s']) * d['sign']
    else:
        raise TypeError('invalid time type', type(x))


@ap.sub()
@ap.opt('t', 'time', required=True)
@ap.arg('file', nargs='*')
@ap.map('time', 'file')
def offset(dt, files):
    __logger__.debug(files)
    dt = parse_time_offset(dt)
    if not dt:
        __logger__.info('# zero offset')
    for fp in iter_path(files):
        __logger__.debug(fp)
        if not fp.endswith('.xml'):
            continue
        et = ElementTree.fromstring(io.IOKit.read_exit(open(fp, 'rb')))
        for d in et.findall('d'):
            a = d.attrib
            p = a['p']
            parts = p.split(',')
            parts[0] = f'{float(parts[0]) + dt:.5f}'
            a['p'] = ','.join(parts)
        io.IOKit.write_exit(open(fp, 'wb'), ElementTree.tostring(et, encoding='UTF-8', xml_declaration=True))
        pm = '+' if dt > 0 else ''
        __logger__.info(f'{pm}{dt:.5f}s {fp}')


def main():
    logging.init_root(fmt=logging.FMT_MESSAGE_ONLY)
    logging.set_root_level('INFO')
    # logging.set_root_level('DEBUG')
    ap.parse()
    ap.run()


if __name__ == '__main__':
    main()
