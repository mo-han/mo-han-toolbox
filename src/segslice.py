#!/usr/bin/env python3
# encoding=utf8


class Segment:
    def __init__(self, value, formatter):
        self._value = value
        self._formatter = formatter or None
        self._form = self._formatter(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new):
        self._value = new
        if self._formatter:
            self._form = self._formatter(self._value)
        else:
            self._form = self._value

    @property
    def formatter(self):
        return self._formatter

    @formatter.setter
    def formatter(self, new):
        self._formatter = new
        if self._formatter:
            self._form = self._formatter(self._value)
        else:
            self._form = self._value

    @property
    def form(self):
        return self._form

    def __eq__(self, other):
        return self.value == other.value and self.formatter == other.formatter


class BaseSegmentList:
    def __init__(self, whole=None, segments: list = None):
        if whole:
            self._whole = whole
            self.decompose()
        elif segments:
            self._segments = segments
            self.compose()
        else:
            self._whole = ''
            self._segments = []

    def decompose(self):
        self.segments = [Segment(self.whole, None)]

    def compose(self):
        segments = self.segments
        whole = segments[0].form
        for e in segments[1:]:
            whole += e.form
        return whole

    @property
    def whole(self):
        return self._whole

    @whole.setter
    def whole(self, new):
        self._whole = new
        self.decompose()

    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, new):
        self._segments = new
        self.compose()


class BracketedSegmentList(BaseSegmentList):
    def __init__(self, left_mark, right_mark, whole=None, segments: list = None):
        super(BracketedSegmentList, self).__init__(whole=whole, segments=segments)
        left_mark_width = len(left_mark)
        right_mark_width = len(right_mark)

        def formatter(value):
            return left_mark + value + right_mark

        def decompose_once(sth):
            stage = 0
            for i in range(len(sth)):
                if stage == 0:
                    search = sth[i:i + left_mark_width]
                    if search == left_mark

        self._left = left_mark
        self._right = right_mark
        self._formatter = formatter

    @property
    def left_mark(self):
        return self._left

    @property
    def right_mark(self):
        return self._right

    @property
    def formatter(self):
        return self._formatter

    def decompose(self):
        left, right = self.left_mark, self.right_mark
        left_width, right_width = len(left), len(right)
        whole = self.whole
        segments = []
        start, middle, end = 0, 0, 0
        wait_right, wait_another_left = False, False
        for i in range(len(whole)):
            pass
