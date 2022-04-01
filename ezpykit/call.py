#!/usr/bin/env python3
from queue import Queue, Empty

from ezpykit.metautil import T
from ezpykit.stdlib import threading


class CallTimeoutError(TimeoutError):
    pass


class BatchCallExceptions(Exception):
    """failed calls stored in `self.args`"""
    pass


class SimpleCall:
    callee: T.Callable = None
    args: tuple = ()
    kwargs: dict
    exception_ignored: T.Union[Exception, T.Tuple[Exception]] = ()
    exception_handler: T.Callable[[Exception], T.Any] = None
    _result_queue = Queue(maxsize=1)
    _exception_queue = Queue(maxsize=1)
    _queue_lock = threading.Lock()
    _counter = 0
    _running_lock = threading.Lock()

    _ok = False
    _result = None
    _exception: T.Optional[Exception] = None

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

    def reset(self):
        self._ok = False
        self._result = None
        self._exception = None

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
        with self._running_lock:
            self._counter += 1
            self.reset()
            try:
                self._result = r = self.callee(*self.args, **self.kwargs)
                self._ok = True
                with self._queue_lock:
                    rq = self._result_queue
                    rq.put(r)
                return r
            except self.exception_ignored:
                pass
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                if isinstance(self.exception_handler, T.Callable):
                    try:
                        self.exception_handler(e)
                    except Exception as he:
                        self._exception = he
                else:
                    self._exception = e
            finally:
                if self._exception:
                    with self._queue_lock:
                        eq = self._exception_queue
                        eq.put(self._exception)
                    if not quiet:
                        raise self._exception

    def get(self, timeout=None, quiet=False):
        rq = self._result_queue
        eq = self._exception_queue
        if not self._running_lock.locked():
            t = threading.thread_factory(name=f'{self!r}: {self.run.__name__}-{self._counter}')(self.run, quiet=quiet)
            t.start()
        try:
            return rq.get(timeout=timeout)
        except Empty:
            try:
                raise eq.get(block=False)
            except Empty:
                raise CallTimeoutError


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
        failed_calls = []
        for call in self.calls:
            call.run(quiet=True)
            if call.ok:
                return call.result
            else:
                failed_calls.append(call)
        raise BatchCallExceptions(*failed_calls)
