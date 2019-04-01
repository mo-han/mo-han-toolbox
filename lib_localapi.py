#!/usr/bin/env python
# -*- coding: utf-8 -*-

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FilePromptAPI:
    """An API that outputs information and receives commands by file(s)"""
    api_dir_name = 'file-prompt-api'

    class Test:
        pass

    def __init__(self, parent_dir, api_dir=api_dir_name):
        self.observer = Observer()
