#!/usr/bin/env python3
from typing import Iterable

from PySide2.QtCore import Signal, Slot


def __ref_sth():
    return Signal, Slot


def signal_connect(signal, slot):
    r = []
    if isinstance(slot, Iterable):
        for i_slot in slot:
            signal.connect(i_slot)
            r.append(i_slot)
    elif slot:
        signal.connect(slot)
        r.append(slot)
    return r


def signal_disconnect(signal, slot=None):
    try:
        if isinstance(slot, Iterable):
            for i_slot in slot:
                signal_disconnect(signal, i_slot)  # nested calling
        elif slot:
            while True:
                signal.disconnect(slot)
        else:
            try:
                signal.disconnect()
            except RuntimeError:
                pass
    except TypeError:
        pass


def signal_batch_connect(mapping: dict):
    r = {}
    for signal, slot in mapping.items():
        r[signal] = signal_connect(signal, slot)
    return r


def signal_reconnect(signal, new=None, old=None):
    signal_disconnect(signal, old)
    if new:
        return signal_connect(signal, new)
    else:
        return []
