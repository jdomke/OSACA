#!/usr/bin/env python3
"""Immediate operand class"""

from osaca.parser import Operand


class Immediate(Operand):
    value = None

    def __init__(self, value):
        super().__init__('immediate')
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.value)
