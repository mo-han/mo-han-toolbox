#!/usr/bin/env python3
import traceback
from typing import Generator

from PySide2.QtCore import QObject, Signal, Slot, QRunnable

from mylib.ex.pyside2.signal import *


class ThreadWorkerError:
    def __init__(self, e: Exception, trace: str):
        self.exception = e
        self.traceback_str = trace


class ThreadWorkerSignal(QObject):
    started = Signal()
    finished = Signal()
    result = Signal(object)
    i_result = Signal(object)
    error = Signal(ThreadWorkerError)


class ThreadWorker(QRunnable):
    def __init__(self, callee, *args, **kwargs):
        super(ThreadWorker, self).__init__()
        self.call_tuple = callee, args, kwargs
        self.signals = ThreadWorkerSignal()

    def connect_signals(self, started=None, finished=None, result=None, i_result=None, error=None):
        s = self.signals
        connect_signal_slot({
            s.started: started, s.finished: finished, s.result: result, s.i_result: i_result, s.error: error
        })

    @Slot()
    def run(self):
        self.signals.started.emit()
        callee, args, kwargs = self.call_tuple
        try:
            r = callee(*args, **kwargs)
            if isinstance(r, Generator):
                for i in r:
                    self.signals.i_result.emit(i)
            else:
                self.signals.result.emit(r)
        except StopIteration as e:
            if e.value:
                self.signals.result.emit(e.value)
                self.signals.error.emit(ThreadWorkerError(e, traceback.format_exc()))
        except Exception as e:
            self.signals.error.emit(ThreadWorkerError(e, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

# class Call:
#     def __init__(self, callee, *args, **kwargs):
#         self.call_tuple = callee, args, kwargs
#
#
# class CallResult:
#     def __init__(self, call: Call = None):
#         self.value = None
#         self.error = None
#         if call:
#             try:
#                 callee, args, kwargs = call.call_tuple
#                 self.value = callee(*args, **kwargs)
#             except Exception as e:
#                 self.error = e
#
#     def set_error(self, e: Exception):
#         self.error = e
#         return self
#
#     @property
#     def ok(self):
#         return not self.error
#
#     @property
#     def is_generator(self):
#         return isinstance(self.value, Generator)
#
#     def __repr__(self):
#         return f'{self.__class__.__name__}({repr(self.value)}, {repr(self.error)})'
#
#
# class WorkerForQThreadTestingStage(QObject):
#     done = Signal()
#     result = Signal(CallResult)
#
#     @Slot()
#     def do(self):
#         print('DEBUG:', self.__class__.__name__, self.do.__name__)
#         try:
#             result = CallResult(self.call)
#             if result.is_generator:
#                 while True:
#                     try:
#                         i = CallResult(Call(next, result.value))
#                     except StopIteration:
#                         self.done.emit()
#                         break
#                     except Exception as e:
#                         self.result.emit(CallResult().set_error(e))
#                         self.done.emit()
#                         break
#                     else:
#                         self.result.emit(i)
#             else:
#                 self.result.emit(result)
#                 self.done.emit()
#         except Exception as e:
#             self.result.emit(CallResult().set_error(e))
#             self.done.emit()
#
#
# def qt_thread_worker_testing_stage(worker_call: Call, worker_class=WorkerForQThreadTestingStage,
#                                    on_thread_start=None, on_thread_finish=None, on_worker_result=None, ):
#     thread = QThread()
#     worker = worker_class()
#     worker.call = worker_call
#
#     for signal, slot in {
#         thread.started: on_thread_start,
#         thread.finished: on_thread_finish,
#         worker.result: on_worker_result,
#     }.items():
#         if slot:
#             if isinstance(slot, Iterable):
#                 for s in slot:
#                     signal.connect(s)
#             else:
#                 signal.connect(slot)
#
#     thread.started.connect(worker.do)
#     thread.finished.connect(thread.deleteLater)
#     worker.done.connect(thread.quit)
#     worker.done.connect(worker.deleteLater)
#
#     worker.moveToThread(thread)
#     thread.start()
#     return thread, worker
