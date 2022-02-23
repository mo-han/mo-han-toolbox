#!/usr/bin/env python3
from ..__common__ import *
from ezpykit.enhance_stdlib.threading import thread_factory


def ez_args_kwargs_str(args, kwargs):
    s_args_kwargs = ', '.join(itertools.chain(
        map(repr, args),
        (f"{k}={repr(v)}" for k, v in kwargs.items()),
    ))
    return s_args_kwargs


class ACall:
    target: T.Callable
    args: tuple
    kwargs: dict
    delta_t: T.Optional[float]
    ok: bool
    result: T.Any
    exception: T.Optional[Exception]
    ignore_exceptions: T.Union[Exception, T.Tuple[Exception]]
    exception_handler: T.Callable[[Exception], T.Any]
    timeout: T.Optional[float]

    def __init__(self, callee, *args, **kwargs):
        self.set_call(callee, *args, **kwargs).set_exceptions().set_timeout().clear()

    def clear(self):
        self.delta_t = None
        self.ok = False
        self.result = None
        self.exception = None
        return self

    def set_call(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        return self

    def set_exceptions(self, ignore_exceptions: T.Union[Exception, T.Tuple[Exception]] = (), exception_handler=None):
        self.ignore_exceptions = ignore_exceptions
        self.exception_handler = exception_handler
        return self

    def set_timeout(self, timeout=None):
        # if timeout and timeout < 0:
        #     raise ValueError('timeout < 0')
        self.timeout = timeout
        return self

    def get_result_blocking(self, *args, **kwargs):
        counter = time.perf_counter
        self.clear()
        t0 = counter()
        try:
            self.result = self.target(*(args or self.args), **(kwargs or self.kwargs))
            self.ok = True
            return self.result
        except self.ignore_exceptions:
            pass
        except Exception as e:
            if not self.exception_handler:
                self.exception = e
                raise e
            else:
                return self.exception_handler(e)
        finally:
            self.delta_t = counter() - t0

    def get_result_timeout(self, *args, **kwargs):
        thread = thread_factory(daemon=True)(self.get_result_blocking, *args, **kwargs)
        thread.start()
        thread.join(self.timeout)  # join will terminate the thread (or not?)
        if self.ok:
            return self.result
        if self.exception:
            raise self.exception
        raise TimeoutError()

    def get_result(self, *args, **kwargs):
        if self.timeout is None:
            return self.get_result_blocking(*args, **kwargs)
        return self.get_result_timeout(*args, **kwargs)

    def __str__(self):
        s_args_kwargs = ez_args_kwargs_str(self.args, self.kwargs)
        s = f'{self.target}({s_args_kwargs})'
        if self.timeout is not None:
            s += f' with timeout={self.timeout}'
        return s


class ALotCall:
    def __init__(self, *calls: T.Union[ACall, T.Iterable[ACall]]):
        self.all_calls_iter = itertools.chain(*[[i] if isinstance(i, ACall) else i for i in calls])

    def any(self, *args, **kwargs):
        return any((call.get_result(*args, **kwargs) for call in self.all_calls_iter))

    def any_result(self, *args, **kwargs):
        for call in self.all_calls_iter:
            r = call.get_result(*args, **kwargs)
            if r:
                return r
