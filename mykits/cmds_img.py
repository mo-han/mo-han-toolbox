#!/usr/bin/env python3
from mylib.easy import *
from ezpykit.stdlib import argparse
from mylib.ext import ostk

apr = argparse.ArgumentParserRigger()
an = apr.an


def main():
    apr.parse()
    apr.run()


an.img = an.l = an.lang = an.v = an.verbose = None


@apr.sub()
@apr.arg(an.img, nargs='?')
@apr.opt(an.l, an.lang, nargs='*')
@apr.true(an.v, an.verbose)
@apr.map(an.img, lang=an.lang, verbose=an.verbose)
def ocr(image=None, lang=None, verbose=False):
    from PIL.ImageGrab import grabclipboard
    from mylib.wrapper.tesseract_ocr import TesseractOCRCLIWrapper
    import yaml
    config = yaml.safe_load(open(os.path.splitext(__file__)[0] + '.yml').read())[ocr.__name__]['tesseract']
    tess = TesseractOCRCLIWrapper(config['bin'])
    if verbose:
        tess.logger.setLevel('DEBUG')
        tess.logger.set_all_handlers_format('# %(message)s')
    lang = lang or config.get('lang')
    image = image or grabclipboard()
    if lang:
        tess.lang(*lang)
    try:
        s = '\r\n'.join(tess.img(image, gray=True).txt().strip().splitlines())
        if s.strip():
            ostk.clipboard.clear().set(s)
        print(s)
    except TypeError:
        print(f'! non-image provided', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
