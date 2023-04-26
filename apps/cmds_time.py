#!/usr/bin/env python3
from oldezpykitext.appkit import *

apr = argparse.ArgumentParserWrapper()
an = apr.an

an.unix_timestamp = an.iso_datetime = ''


@apr.sub(aliases=['u2i'], help='UTC unix timestamp to iso8601')
@apr.arg(an.unix_timestamp, type=float, nargs='?', default=time.time())
@apr.map(an.unix_timestamp)
def unix2iso(t):
    r = datetime.datetime.utcfromtimestamp(t).isoformat()
    print(r)
    return r


@apr.sub(aliases=['i2u'], help='UTC iso8601 to unix timestamp')
@apr.arg(an.iso_datetime)
@apr.map(an.iso_datetime)
def iso2unix(s):
    r = datetime.from_iso_format(s).timestamp()
    print(r)
    return r


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
