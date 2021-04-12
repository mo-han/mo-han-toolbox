#!/usr/bin/env python3
from mylib.ez import argparse
from mylib.ez import *
from mylib.ex import fstk
from mylib.ex import ostk

apr = argparse.ArgumentParserRigger()
an = apr.an


def main():
    argv = sys.argv
    if len(argv) < 2:
        argv.append('-h')
    apr.parse()
    apr.run()


an.img = an.l = an.lang = None


@apr.sub()
@apr.arg(an.img, nargs='?')
@apr.opt(an.l, an.lang, nargs='*')
def ocr(image=None, lang=None):
    from PIL.ImageGrab import grabclipboard
    from mylib.wrapper.tesseract_ocr import TesseractOCRCLIWrapper
    import yaml
    config = yaml.safe_load(open(os.path.splitext(__file__)[0] + '.yml').read())[ocr.__name__]['tesseract']
    tess = TesseractOCRCLIWrapper(config['bin'])
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
