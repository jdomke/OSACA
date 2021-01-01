#!/usr/bin/env python3
"""Identifier operand class"""

from osaca.parser import Operand


class Identifier(Operand):
    name = None

    def __init__(self, name):
        super().__init__('label')
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)
