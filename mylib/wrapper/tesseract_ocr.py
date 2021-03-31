#!/usr/bin/env python3
from mylib.ez import *


class TesseractOCRCLIWrapper:
    def __init__(self, tesseract_executable_path: str):
        self.exec = tesseract_executable_path
    