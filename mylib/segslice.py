#!/usr/bin/env python3
# encoding=utf8


class Segment:
    def __init__(self, value, formatter):
        self._value = value
        self._formatter = formatter
        if self._formatter:
            self._form = self._formatter(self._value)
        else:
            self._form = self._value

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
            self.redivide()
        elif segments:
            self._segments = segments
            self.reunion()
        else:
            self._whole = ''
            self._segments = []

    def redivide(self):
        self.segments = [Segment(self.whole, None)]

    def reunion(self):
        segments = self.segments
        whole = segments[0].form
        for e in segments[1:]:
            whole += e.form
        self.whole = whole

    @property
    def whole(self):
        return self._whole

    @whole.setter
    def whole(self, new):
        self._whole = new
        self.redivide()

    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, new):
        self._segments = new
        self.reunion()


class BracketedSegmentList(BaseSegmentList):
    def __init__(self, brackets: tuple, whole=None, segments: list = None):
        left, right = brackets

        def formatter(value):
            return left + value + right

        self._left = left
        self._right = right
        self._formatter = formatter
        super(BracketedSegmentList, self).__init__(whole=whole, segments=segments)

    @property
    def left_mark(self):
        return self._left

    @property
    def right_mark(self):
        return self._right

    @property
    def formatter(self):
        return self._formatter

    def redivide(self):
        i = preamble_stop = start = stop = stage = 0
        left = self.left_mark
        left_n = len(left)
        right = self.right_mark
        right_n = len(right)
        w = self.whole
        seg_l = []
        while w:
            while i < len(w):
                if stage == 0:
                    search_l = w[i:i + left_n]
                    if search_l == left:
                        preamble_stop = i
                        start = i + left_n
                        i += left_n
                        stage += 1
                    else:
                        i += 1
                elif stage == 1:
                    search_r = w[i:i + right_n]
                    if search_r == right:
                        stop = i
                        i += right_n
                        stage += 1
                    else:
                        i += 1
                elif stage == 2:
                    search_l = w[i:i + left_n]
                    search_r = w[i:i + right_n]
                    if search_l == left:
                        seg_l.append(Segment(w[:preamble_stop], None))
                        seg_l.append(Segment(w[start:stop], self.formatter))
                        w = w[stop + right_n:]
                        i = stage = preamble_stop = start = stop = 0
                        break
                    elif search_r == right:
                        stop = i
                        i += right_n
                    else:
                        i += 1
            else:
                if stop:
                    if preamble_stop:
                        seg_l.append(Segment(w[:preamble_stop], None))
                    seg_l.append(Segment(w[start:stop], self.formatter))
                    w = w[stop + right_n:]
                else:
                    seg_l.append(Segment(w, None))
                    w = None
                    break
                i = stage = preamble_stop = start = stop = 0
        self._segments = seg_l
