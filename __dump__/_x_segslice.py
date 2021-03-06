#!/usr/bin/env python3
# encoding=utf8


class Formatter:
    def __init__(self, fmt_func=lambda x: x, mark=None):
        self._fmt_func = fmt_func
        self._mark = mark

    def __call__(self, *args, **kwargs):
        return self._fmt_func(*args, **kwargs)

    def __hash__(self):
        return hash(self._fmt_func)

    def __eq__(self, other):
        return hash(self) == hash(other) and self.mark == other.mark

    @property
    def mark(self):
        return self._mark


class Segment:
    def __init__(self, value, formatter: Formatter):
        self._value = value
        self._formatter = formatter
        self._form = self._formatter(self._value)

    def __str__(self):
        return 'segment({}, {})'.format(self.signature, self.value)

    def __eq__(self, other):
        return self.value == other.value and self.formatter == other.formatter

    def __hash__(self):
        return hash(self.value) + hash(self.formatter)

    @property
    def mark(self):
        return self.formatter.mark

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
    def signature(self):
        return self.formatter.mark

    @property
    def repr(self):
        return self._form


class BaseSegments:
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

    def __getitem__(self, item):
        return self.segments[item]

    def redivide(self):
        self.segments = [Segment(self.whole, Formatter())]

    def reunion(self):
        segments = self.segments
        whole = segments[0].repr
        for e in segments[1:]:
            whole += e.repr
        self.whole = whole

    @property
    def is_original(self):
        return len(self.segments) == 1 and (self.segments[0].formatter is None or self.segments[0].value == self.whole)

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

    def __repr__(self):
        head = super(BaseSegments, self).__repr__()
        body = '\n'.join(seg.repr for seg in self.segments)
        return '{}\n{}'.format(head, body)


class BracketedSegments(BaseSegments):
    def __init__(self, brackets: tuple, whole=None, segments: list = None):
        left, right = brackets

        def fmt_func(value):
            return left + value + right

        self._left = left
        self._right = right
        self._formatter = Formatter(fmt_func, left + right)
        super(BracketedSegments, self).__init__(whole=whole, segments=segments)

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
        empty_fmt = Formatter()
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
                        if preamble_stop:
                            seg_l.append(Segment(w[:preamble_stop], empty_fmt))
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
                        seg_l.append(Segment(w[:preamble_stop], empty_fmt))
                    seg_l.append(Segment(w[start:stop], self.formatter))
                    w = w[stop + right_n:]
                else:
                    seg_l.append(Segment(w, empty_fmt))
                    w = None
                    break
                i = stage = preamble_stop = start = stop = 0
        self._segments = seg_l
