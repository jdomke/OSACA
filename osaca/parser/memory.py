#!/usr/bin/env python3
"""Memory operand class"""

from osaca.parser import Operand


class Memory(Operand):
    offset = None
    base = None
    index = None
    scale = 1
    mask = None
    pre_indexed = False
    post_indexed = False

    def __init__(
        self,
        base=None,
        offset=None,
        index=None,
        scale=1,
        mask=None,
        pre_indexed=False,
        post_indexed=False,
    ):
        super().__init__('memory')
        self.base = base
        self.offset = offset
        self.index = index
        self.scale = scale
        self.mask = mask
        self.pre_indexed = pre_indexed
        self.post_indexed = post_indexed

    def __str__(self):
        repr_string = str(self.offset) if self.offset else ''
        repr_string += '('
        repr_string += str(self.base) if self.base else ''
        repr_string += (
            ',{}{}'.format(self.index, ',' + str(self.scale) if self.scale != 1 else '')
            if self.index
            else ''
        )
        repr_string += ')'
        repr_string += '{{{}}}'.format(self.mask) if self.mask else ''
        repr_string += ' (pre indexed)' if self.pre_indexed else ''
        repr_string += ' (post indexed)' if self.post_indexed else ''
        return repr_string

    def __repr__(self):
        indx_str = (
            ' (pre indexed)'
            if self.pre_indexed
            else ' (post indexed)'
            if self.post_indexed
            else ''
        )
        mask_str = '{{{}}}'.format(repr(self.mask)) if self.mask else ''
        return '{}({})'.format(
            self.__class__.__name__,
            '{}({},{},{}){}{}'.format(
                repr(self.offset),
                repr(self.base),
                repr(self.index),
                repr(self.scale),
                mask_str,
                indx_str,
            ),
        )
