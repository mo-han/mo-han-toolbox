#!/usr/bin/env python3
# encoding=utf8


class Segment:
    def __init__(self, value, formatter):
        self.value = value
        self.formatter = formatter

    def format(self):
        return self.formatter(self.value)


class BaseSegmentList:
    def __init__(self, whole=None, segments: list = None):
        if whole:
            self._whole = whole
            self._decompose()
        elif segments:
            self._segments = segments
            self._compose()
        else:
            self._whole = ''
            self._segments = []

    @staticmethod
    def formatter(segment: Segment):
        return segment.value

    @staticmethod
    def decomposer(whole):
        pass

    @staticmethod
    def composer(segments: list):
        pass

    def _decompose(self):
        for 

    def _compose(self):
        pass

    @property
    def entirety(self):
        return self._whole

    @entirety.setter
    def entirety(self, new):
        self._whole = new
        self._decompose()

    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, new):
        self._segments = new
        self._compose()


class BracketedSegmentList(BaseSegmentList):
    def __init__(self, left, right, whole=None, segments: list = None):
        super(BracketedSegmentList, self).__init__(whole=whole, segments=segments)
        self._left = left
        self._right = right

    def _decompose(self):
        pass
