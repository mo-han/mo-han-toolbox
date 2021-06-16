Document is lacking, but the source code is easy to understand.

#### cwebp

- use cwebp in PATH
- support feeding image file data via stdin pipe
- return dict including metadata
- set options via kwargs
- resize with float scale (keep aspect)

Example:
```python
from mylib.wrapper import cwebp

cwebp.image_to_bytes
cwebp.image_from_bytes

src = 'src/image/filepath' or b'image file bytes'
dst = '-' or 'dst/image/filepath'  # '-' get cwebp output image bytes from stdout and put it into dict
cwebp.cwebp_call(src, q=50, resize=0.5, print_ssim=True)
```
output something like this:
```python
{'kwargs': {'q': 50, 'print_ssim': True, 'resize': (334, 482)},
 'out': b'A LONG BYTES OF THE OUTPUT IMAGE FILE',
 'msg': ["Saving file '-'",
  'File:      -',
  'Dimension: 334 x 482',
  'Output:    8352 bytes Y-U-V-All-PSNR 39.53 99.00 99.00   41.29 dB',
  '           (0.42 bpp)',
  'block count:  intra4:        256  (39.32%)',
  '              intra16:       395  (60.68%)',
  '              skipped:       388  (59.60%)',
  'bytes used:  header:            121  (1.4%)',
  '             mode-partition:   1174  (14.1%)',
  ' Residuals bytes  |segment 1|segment 2|segment 3|segment 4|  total',
  '    macroblocks:  |       1%|      10%|      27%|      62%|     651',
  '      quantizer:  |      52 |      49 |      42 |      34 |',
  '   filter level:  |      16 |      10 |       7 |       5 |',
  'SSIM: B:19.07 G:19.07 R:19.07 A:99.00  Total:20.32'],
 'cmd': ['cwebp',
  '-q',
  '50',
  '-print_ssim',
  '-resize',
  '334',
  '482',
  '-o',
  '-',
  '--',
  '-'],
 'code': 0,
 'ok': True,
 'src': {'path': '-', 'size': 30230, 'width': 667, 'height': 964},
 'dst': {'q': 50.0,
  'scale': 0.5,
  'path': '-',
  'width': 334,
  'height': 482,
  'size': 8352,
  'psnr': {'y': 39.53, 'u': 99.0, 'v': 99.0, 'all': 41.29},
  'ssim': {'b': 19.07, 'g': 19.07, 'r': 19.07, 'a': 99.0, 'total': 20.32},
  'compress': 0.276}}
```

#### tesseract_ocr

- support feeding image via stdin pipe
- get output data via stdout pipe
- so no temp file created
- set input image with filepath or file bytes or PIL Image object or nd-array
- set options via kwargs
- output data as dict in proper structure
- fluent interface/api

Example:
```python
from mylib.wrapper import tesseract_ocr

t = tesseract_ocr.TesseractOCRCLIWrapper('path/of/tesseract/executable')
# input image could be set via different methods for different data type
t.set_image_array
t.set_image_bytes
t.set_image_object
t.set_image_file

t.set_language('chi_sim', 'eng').set_image_bytes(b'IMAGE FILE BYTES').get_ocr_tsv_to_json()
```
output something like this:
```python
[{'text': '名',
  'confidence': 0.91,
  'box': ((320, 10), (333, 10), (333, 23), (320, 23)),
  'page_block_paragraph_line_word_level': (1, 1, 1, 1, 1, 5)},
 {'text': '称',
  'confidence': 0.87,
  'box': ((320, 28), (333, 28), (333, 40), (320, 40)),
  'page_block_paragraph_line_word_level': (1, 1, 1, 1, 2, 5)},
 {'text': '修改',
  'confidence': 0.9,
  'box': ((320, 336), (333, 336), (333, 366), (320, 366)),
  'page_block_paragraph_line_word_level': (1, 1, 1, 1, 3, 5)},
 {'text': '日',
  'confidence': 0.96,
  'box': ((320, 372), (333, 372), (333, 379), (320, 379)),
  'page_block_paragraph_line_word_level': (1, 1, 1, 1, 4, 5)},
 {'text': '期',
  'confidence': 0.96,
  'box': ((320, 387), (333, 387), (333, 395), (320, 395)),
  'page_block_paragraph_line_word_level': (1, 1, 1, 1, 5, 5)},
 {'text': ' ',
  'confidence': 0.95,
  'box': ((0, 195), (0, 195), (0, 224), (0, 224)),
  'page_block_paragraph_line_word_level': (1, 2, 1, 1, 1, 5)},
 {'text': 'label_cn.txt',
  'confidence': 0.8,
  'box': ((283, 38), (295, 38), (295, 120), (283, 120)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 1, 1, 5)},
 {'text': '2019/8/5',
  'confidence': 0.87,
  'box': ((281, 337), (294, 337), (294, 401), (281, 401)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 1, 2, 5)},
 {'text': '15:24',
  'confidence': 0.95,
  'box': ((283, 408), (294, 408), (294, 446), (283, 446)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 1, 3, 5)},
 {'text': '2019/8/5',
  'confidence': 0.91,
  'box': ((254, 337), (267, 337), (267, 401), (254, 401)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 2, 3, 5)},
 {'text': '15:24',
  'confidence': 0.96,
  'box': ((256, 408), (267, 408), (267, 446), (256, 446)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 2, 4, 5)},
 {'text': '2019/8/5',
  'confidence': 0.89,
  'box': ((227, 337), (240, 337), (240, 401), (227, 401)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 3, 3, 5)},
 {'text': '15:24',
  'confidence': 0.96,
  'box': ((229, 408), (240, 408), (240, 446), (229, 446)),
  'page_block_paragraph_line_word_level': (1, 3, 1, 3, 4, 5)}]
```