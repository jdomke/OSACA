#!/usr/bin/env python3
"""Register operand class"""

from osaca.parser import Operand


class Register(Operand):
    prefix = None
    name = None
    lanes = None
    shape = None
    width = None
    index = None
    mask = None
    zeroing = False

    def __init__(
        self,
        name,
        prefix=None,
        lanes=None,
        shape=None,
        width=None,
        index=None,
        mask=None,
        zeroing=False,
    ):
        super().__init__('register')
        self.prefix = prefix
        self.name = name
        self.lanes = lanes
        self.shape = shape
        self.width = width
        self.index = index
        self.mask = mask
        self.zeroing = zeroing

    def __str__(self):
        repr_string = self.prefix if self.prefix else ''
        repr_string += self.name
        if self.lanes and self.shape:
            repr_string += '.' + self.lanes + self.shape
        else:
            repr_string += '.' + self.shape if self.shape else ''
        repr_string += '[{}]'.format(self.index) if self.index else ''
        repr_string += '{{{}}}'.format(self.mask) if self.mask else ''
        repr_string += '{z}' if self.zeroing else ''
        repr_string += '({} bit)'.format(self.width) if self.width else ''
        return repr_string

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))
