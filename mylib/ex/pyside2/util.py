#!/usr/bin/env python3
from mylib.easy import *
from mylib.easy import T


class EzQtObjectMixin:
    def __init__(self, widget):
        self.widget = widget

    def set(self, **kwargs):
        for name, value in kwargs.items():
            setter = self.__setter_method__(name)
            if isinstance(value, EzArguments):
                setter(*value.args, **value.kwargs)
            else:
                setter(value)
        return self

    def get(self, *args: str, **kwargs):
        r = []
        for name in args:
            name = ez_snake_case_to_camel_case(name)
            getter = self.__getter_method__(name)
            r.append(getter())
        for name, value in kwargs.items():
            name = ez_snake_case_to_camel_case(name)
            getter = self.__getter_method__(name)
            if isinstance(value, EzArguments):
                r.append(getter(*value.args, **value.kwargs))
            else:
                r.append(getter(value))
        return r

    @functools.lru_cache()
    def __setter_method__(self, name):
        return getattr(self, ez_snake_case_to_camel_case('set_' + name))

    @functools.lru_cache()
    def __getter_method__(self, name):
        return getattr(self, ez_snake_case_to_camel_case(name))

    def __the_method_factory__(self, name: str):
        name_without_the = str_remove_prefix(name, 'the_')

        def _the_func(x=..., *args, **kwargs):
            if x is ...:
                getter = self.__getter_method__(name_without_the)
                return getter(*args, **kwargs)
            else:
                setter = self.__setter_method__(name_without_the)
                setter(*args, **kwargs)
                return self

        _the_func.__name__ = name
        self.__dict__[name] = _the_func
        return _the_func

    def __getattr__(self, name: str):
        if name.startswith('the_'):
            return self.__the_method_factory__(name)
        raise AttributeError(name)

    def the_qss(self, value=..., selector=None):
        if value is ...:
            return self.styleSheet()
        else:
            self.setStyleSheet(ez_qss(value, selector=selector))
            return self


def ez_qt_obj(q_obj):
    original_class = q_obj.__class__

    class NewClass(original_class, EzQtObjectMixin):
        pass

    NewClass.__name__ = 'Ez' + original_class.__name__
    q_obj.__class__ = NewClass
    return q_obj


def ez_qss(value, selector=None):
    if isinstance(value, dict):
        style_sheet = '; '.join(f'{k.replace("_", "-")}: {v}' for k, v in value.items())
    elif isinstance(value, str):
        style_sheet = value
    elif isinstance(value, T.Iterable):
        style_sheet = '; '.join(i for i in value)
    else:
        raise TypeError('style')
    if selector:
        if hasattr(selector, '__name__'):
            selector = selector.__name__
        style_sheet = f'{selector} {{{style_sheet}}}'
    return style_sheet
