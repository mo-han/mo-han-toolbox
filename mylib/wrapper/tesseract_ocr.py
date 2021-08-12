#!/usr/bin/env python3
from mylib.ex.PIL import *
from mylib.easy import *
from mylib.easy import logging


class TesseractOCRCLIWrapper:
    def __init__(self, tesseract_executable_path: str):
        self.exec = tesseract_executable_path
        self.lang_args = CLIArgumentsList()
        self.cmd = CLIArgumentsList()
        self.image_bytes = None
        self.logger = logging.ez_get_logger(f'{__name__}.{self.__class__.__name__}')
        self.set_all_languages()

    def get_all_languages(self):
        lang = set()
        for fn in os.listdir(os.path.join(os.path.dirname(self.exec), 'tessdata')):
            m = re.match(r'(.+)\.(traineddata|user-patterns|user-words)$', fn)
            if m:
                lang.add(m.group(1))
        lang.remove('osd')
        return lang

    def set_all_languages(self):
        self.set_language(*self.get_all_languages())
        return self

    @property
    def version(self):
        cmd = CLIArgumentsList(self.exec, version=True)
        ot = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode()
        return ot

    def __repr__(self):
        return f'{super().__repr__()} ({self.exec})'

    def _init_cmd(self, input_file='stdin'):
        self.cmd.clear()
        self.cmd.add(self.exec, input_file, 'stdout')

    def _run_cmd(self):
        self.cmd.add(*self.lang_args)
        self.logger.debug(self.cmd)
        r = subprocess.run(self.cmd, input=self.image_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.stdout = r.stdout
        self.stderr = r.stderr

    def set_image_file(self, image_path):
        self.image_bytes = None
        self._init_cmd(image_path)
        return self

    def set_image_bytes(self, image_bytes):
        self.image_bytes = image_bytes
        # print('image_bytes', len(image_bytes))
        self._init_cmd()
        return self

    def set_image_object(self, image: Image.Image, gray=False):
        """PIL Image object"""
        # with io.BytesIO() as bytes_io:
        #     if gray:
        #         image = image.convert('LA')
        #     # tesseract seem not support DIB, convert to PNG
        #     image.save(bytes_io, format={'DIB': 'PNG'}.get(image.format, image.format) or 'PNG')
        #     self.set_image_bytes(bytes_io.getvalue())
        self.set_image_bytes(save_image_to_bytes(image, 'PNG'))
        return self

    def set_image_array(self, nd_array, mode=None):
        """for the param `mode`, refer to `Image.fromarray`"""
        self.set_image_object(Image.fromarray(nd_array, mode=mode))
        return self

    def set_image(self, image, **kwargs):
        if isinstance(image, Image.Image):
            return self.set_image_object(image, **kwargs)
        if isinstance(image, bytes):
            return self.set_image_bytes(image)
        if isinstance(image, str):
            return self.set_image_file(image)
        try:
            return self.set_image_array(image)
        except AttributeError:
            raise TypeError('image', (str, bytes, Image.Image, 'nd-array'))

    def get_ocr_tsv_to_json(self, *, skip_non_text: bool = True, confidence_threshold: float = None, **kwargs):
        cells = self.get_ocr_tsv(**kwargs)
        headers = ['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num',
                   'left', 'top', 'width', 'height', 'conf', 'text']
        if cells.pop(0) != headers:
            raise ValueError('headers mismatch', headers)
        r = []
        for level, page, block, par, line, word, left, top, width, height, conf, text in cells:
            if conf == '-1':
                if skip_non_text:
                    continue
                else:
                    conf = -1
            else:
                conf = int(conf) / 100
            if confidence_threshold is not None and conf < confidence_threshold:
                continue
            page_block_paragraph_line_word_level = [int(x) for x in [page, block, par, line, word, level]]
            left, top, width, height = int(left), int(top), int(width), int(height)
            r.append({'text': text, 'confidence': conf,
                      'box': [[left, top], [left + width, top], [left + width, top + height], [left, top + height]],
                      'page_block_paragraph_line_word_level': page_block_paragraph_line_word_level})
        return r

    def get_ocr_tsv(self, **kwargs):
        self.cmd.add(**kwargs)
        self.cmd.add('tsv')
        self._run_cmd()
        o = self.stdout.decode()
        cells = [row.split('\t') for row in o.splitlines()]
        self.logger.debug(cells)
        return cells

    def get_ocr_text(self, **kwargs):
        self.cmd.add(**kwargs)
        self._run_cmd()
        return self.stdout.decode()

    def set_language(self, *lang: str):
        self.lang_args.clear()
        if lang:
            self.lang_args.add(l='+'.join(lang))
        return self

    img = set_image
    lang = set_language
    txt = get_ocr_text
    json = get_ocr_tsv_to_json
