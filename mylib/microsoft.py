#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import win32com.client
import pywintypes


class MicrosoftOfficeWordCOM:
    # reference code from https://blog.csdn.net/baidu_39416074/article/details/80926443
    """Microsoft Office Word COM Wrap."""

    def __init__(self, filepath=None, visible=False):
        # self._word = win32com.client.Dispatch('Word.Application')  # 此处使用的是Dispatch，原文中使用的DispatchEx会报错
        self._word = win32com.client.DispatchEx('Word.Application')
        self._word.Visible = visible  # 后台运行，不显示
        self._word.DisplayAlerts = visible  # 不警告
        if filepath:
            self._filepath = filepath
            if os.path.exists(self._filepath):
                self._doc = self._word.Documents.Open(filepath)
            else:
                self._doc = self._word.Documents.Add()  # 创建新的文档
                self._doc.SaveAs(filepath)
        else:
            self._doc = self._word.Documents.Add()
            self._filepath = ''

    @property
    def app(self):
        return self._word

    @property
    def doc(self):
        return self._doc

    @property
    def filepath(self):
        return self._filepath

    def insert_at_top(self, text):
        rng = self._doc.Range()
        rng.InsertAfter('\n' + text)

    def insert_at_bottom(self, text):
        rng = self._doc.Range(0, 0)
        rng.InsertBefore(text + '\n')

    def insert(self, position, text):
        rng = self._doc.Range(0, position)
        if position == 0:
            rng.InsertAfter(text)
        else:
            rng.InsertAfter('\n' + text)

    def replace(self, old, new):
        self._word.Selection.Find.ClearFormatting()
        self._word.Selection.Find.Replacement.ClearFormatting()
        # (old, 区分大小写, 全字匹配, 使用通配符, 同音, 查找单词的各种形式, 向文档尾部搜索, 1:回绕, 带格式的文本, new, 1:单个/2:全部)
        self._word.Selection.Find.Execute(old, False, False, False, False, False, True, 1, True, new, 2)

    def replace_wildcard(self, string, new_string):
        self._word.Selection.Find.ClearFormatting()
        self._word.Selection.Find.Replacement.ClearFormatting()
        self._word.Selection.Find.Execute(string, False, False, True, False, False, False, 1, False, new_string, 2)

    def open(self, filepath):
        self._doc = self._word.Documents.Open(filepath)
        self._filepath = filepath

    def save(self):
        self._doc.Save()

    def save_as(self, filepath):
        self._doc.SaveAs(filepath)

    def close(self, save=True):
        if save: self.save()
        self._word.Documents.Close()
        self._filepath = ''

    def quit(self, save=True):
        try:
            self.close(save=save)
        except pywintypes.com_error:
            pass
        self._word.Quit()
