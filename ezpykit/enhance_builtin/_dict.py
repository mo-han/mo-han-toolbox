#!/usr/bin/env python3
import collections.abc
from ezpykit.allinone.metautil import DecoListOfNameMagicVar

__all__ = DecoListOfNameMagicVar()
_Type_Mapping = collections.abc.Mapping


@__all__
def recursive_update_dict(d: dict, m: collections.abc.Mapping, factory_class=dict):
    for k, v in m.items():
        if isinstance(v, _Type_Mapping):
            d[k] = recursive_update_dict(d.get(k, factory_class()), v)
        else:
            d[k] = v
    return d


@__all__
class ListKeyDict(dict):
    @staticmethod
    def _key_is_list(key):
        return isinstance(key, list)

    def __contains__(self, key):
        if not self._key_is_list(key):
            return super().__contains__(key)
        try:
            self._getitem_by_list_key(key)
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        if not self._key_is_list(key):
            return super().__getitem__(key)
        return self._getitem_by_list_key(key)

    def _getitem_by_list_key(self, key: list):
        error = KeyError(key)
        i = self
        for k in key:
            try:
                i = i[k]
            except KeyError:
                raise error
            except TypeError as e:
                if e.args[0].endswith('is not subscriptable'):
                    raise error
        return i

    def __setitem__(self, key, value):
        if not self._key_is_list(key):
            super().__setitem__(key, value)
        else:
            self._setitem_by_list_key(key, value)

    def _setitem_by_list_key(self, key: list, value):
        i = self
        for k in key[:-1]:
            try:
                i = i[k]
            except KeyError:
                new = self.__class__()
                i[k] = new
                i = new
        i[key[-1]] = value

    def get(self, key, default=None):
        if not self._key_is_list(key):
            return super().get(key, default)
        try:
            return self._getitem_by_list_key(key)
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        if not self._key_is_list(key):
            return super().setdefault(key, default)
        try:
            return self._getitem_by_list_key(key)
        except KeyError:
            self._setitem_by_list_key(key, default)
            return default


def temp_test():
    import sys

    print(__all__)
    d = ListKeyDict({1: {3: {5: 'hi'}}})
    print(isinstance(d, collections.abc.Mapping))
    kl = [1, 3, 5]
    wrong = [1, 2]
    print('[]:', d[kl])
    print('get:', d.get(kl))
    try:
        d[wrong]
    except:
        print(sys.exc_info())
    print('get:', d.get(wrong, 'wrong'))
    print('setdefault', d.setdefault(wrong, 'wrong set'))
    d[[2, 4, 6]] = 'bye'
    print(d)
    print(type(d[[2, 4]]))
    print([2, 4, 6] in d)
    print([2, 3, 4] in d)
    recursive_update_dict(d, {2: 22, 1: {4: 4444, 3: {6: 666666}}}, ListKeyDict)
    print(d, type(d[[1, 3]]))


if __name__ == '__main__':
    temp_test()
