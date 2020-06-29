#!/usr/bin/env python3
# encoding=utf8

import serial
from mylib import tricks


def short_serial_port(port: str, baudrate: int = 9600, **kwargs):
    p = serial.Serial(port=port, baudrate=baudrate, **kwargs)
    logger = tricks.get_logger('{} shorter'.format(p.name))
    while True:
        b = p.read_all()
        if b:
            logger.info(b)
            p.write(b)
