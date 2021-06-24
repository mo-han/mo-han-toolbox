#!/usr/bin/env python3
from typing import Iterable


def connect_signal_slot(mapping: dict):
    for signal, slot in mapping.items():
        if isinstance(slot, Iterable):
            for i_slot in slot:
                signal.connect(slot)
        elif slot:
            signal.connect(slot)
