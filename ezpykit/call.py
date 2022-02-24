#!/usr/bin/env python3
from ezpykit.base import T


class SimpleCall:
    callee: T.Callable = None
    args: tuple = ()
    kwargs: dict
    exception_ignored: T.Union[Exception, T.Tuple[Exception]] = ()
    exception_handler: T.Callable[[Exception], T.Any] = None
    _ok = False
    _result = None
    _exception: Exception = None

    def __init__(self, callee: T.Union[T.Callable, T.Dict], *args, **kwargs):
        self.kwargs = {}
        if isinstance(callee, T.Callable):
            self.callee = callee
            self.args = args
            self.kwargs = kwargs
        elif isinstance(callee, T.Dict):
            for k in ('callee', 'args', 'kwargs', 'exception_ignored', 'exception_handler'):
                if k in callee:
                    setattr(self, k, callee[k])
        else:
            raise TypeError('callee', T.Union[T.Callable, T.Dict], type(callee))

    @property
    def args_str(self):
        return ', '.join([*map(repr, self.args), *(f"{k}={repr(v)}" for k, v in self.kwargs.items())])

    def __repr__(self):
        s = f'{self.__class__.__name__}: '
        if isinstance(self.callee, T.Callable):
            s += f'{self.callee.__name__ if hasattr(self.callee, "__name__") else self.callee}'
        s += f'({self.args_str})'
        return s

    @property
    def ok(self):
        return self._ok

    @property
    def result(self):
        return self._result

    @property
    def exception(self):
        return self._exception

    def run(self, quiet=False):
        self._ok = False
        try:
            self._result = self.callee(*self.args, **self.kwargs)
            self._ok = True
            return self._result
        except self.exception_ignored:
            pass
        except Exception as e:
            if isinstance(self.exception_handler, T.Callable):
                try:
                    self.exception_handler(e)
                except Exception as he:
                    self._exception = he
                    if not quiet:
                        raise he
            else:
                self._exception = e
            if not quiet:
                raise e


class BatchCall:
    calls: T.List[SimpleCall]

    def __init__(self, calls: T.Iterable[T.Union[SimpleCall, T.Dict]], ignore_invalid=False):
        cl = self.calls = []
        for x in calls:
            if isinstance(x, SimpleCall):
                cl.append(x)
            elif isinstance(x, T.Dict):
                c = SimpleCall(x)
                cl.append(c)
            elif ignore_invalid:
                continue
            else:
                raise TypeError('calls item', (SimpleCall, T.Union[SimpleCall, T.Dict], type(x)))

    def first_result(self):
        for call in self.calls:
            call.run(quiet=True)
            if call.ok:
                return call.result
        raise ValueError('all calls failed, nothing returned')
