#!/usr/bin/env python3
import sys
import traceback
from typing import Generator

from PySide2.QtCore import QObject, QRunnable, QThreadPool

from .signal import *


def __ref_sth():
    return


class EzQtThreadWorkerError:
    def __init__(self, e: Exception, trace: str):
        self.exception = e
        self.trace = trace

    def print_trace(self, *args, file=sys.stderr, **kwargs):
        print(self.trace, *args, file=file, **kwargs)


class EzQtThreadWorker(QObject, QRunnable):
    signal_started = Signal()
    signal_finished = Signal()
    signal_result = Signal(object)
    signal_i_result = Signal(object)
    signal_error = Signal(EzQtThreadWorkerError)

    def __init__(self, callee, *args, **kwargs):
        super(EzQtThreadWorker, self).__init__()
        QRunnable.__init__(self)
        self.call_tuple = callee, args, kwargs

    def set_auto_delete(self, value=True):
        self.setAutoDelete(value)
        return self

    def set_parent(self, parent):
        self.setParent(parent)
        return self

    def connect_signals(self, started=None, finished=None, result=None, i_result=None, error=None):
        ez_qt_signal_map({
            self.signal_started: started, self.signal_finished: finished, self.signal_result: result,
            self.signal_i_result: i_result, self.signal_error: error
        })
        return self

    def start_in_pool(self, thread_pool: QThreadPool, priority: int = 0):
        thread_pool.start(self, priority=priority)
        return self

    @Slot()
    def run(self):
        self.signal_started.emit()
        callee, args, kwargs = self.call_tuple
        try:
            r = callee(*args, **kwargs)
            if isinstance(r, Generator):
                while True:
                    ir = next(r)
                    self.signal_i_result.emit(ir)
                # for i in r:
                #     self.signal_i_result.emit(i)
            else:
                self.signal_result.emit(r)
        except StopIteration as e:
            if e.value:
                self.signal_result.emit(e.value)
                # self.signal_error.emit(ThreadWorkerError(e, traceback.format_exc()))
        except Exception as e:
            self.signal_error.emit(EzQtThreadWorkerError(e, traceback.format_exc()))
        finally:
            self.signal_finished.emit()
        return self
