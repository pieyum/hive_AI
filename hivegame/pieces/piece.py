# piece.py
# Classes representing playing pieces

import abc
from collections import namedtuple
from typing import Optional

from hivegame.hive_utils import HiveException
import logging

from hivegame.utils import hexutil

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from hivegame.hive import Hive

class HivePiece(namedtuple("HivePiece", "color kind number"), metaclass=abc.ABCMeta):
    """Representation of Playing Piece"""

    @abc.abstractmethod
    def __new__(cls, color, kind, number):
        return super().__new__(cls, color, kind, number)

    def __repr__(self):
        return "%s%s%s" % (self.color, "?", self.number)
    
    def check_blocked(self, hive: 'Hive', pos: hexutil.Hex) -> bool:
        """
        Check if the piece is blocked by a beetle. Returns True if blocked
        """
        assert hive.level.get_tile_content(pos)
        if hive.level.get_tile_content(pos)[-1] == self:
            return False
        return True

    @abc.abstractproperty
    def kind(self):
        return "?"
    
    @abc.abstractmethod
    def validate_move(self, hive: 'Hive', end_cell: hexutil.Hex, pos: hexutil.Hex):
        return

    @abc.abstractmethod
    def available_moves(self, hive: 'Hive', pos: hexutil.Hex):
        return []

    @abc.abstractmethod
    def available_moves_vector(self, hive: 'Hive', pos: hexutil.Hex):
        return []

    def index_to_target_cell(self, hive: 'Hive', number: int, pos: hexutil.Hex) -> 'hexutil.Hex':
        aval_moves = self.available_moves(hive, pos)
        if len(aval_moves) <= number or number >= self.move_vector_size:
            print(self)
            print("check_blocked: {}".format(self.check_blocked(hive, pos)))
            print("len aval moves: {}, number: {}, move_vector_size: {}".format(len(aval_moves), number, self.move_vector_size))
            raise HiveException("moving piece with action number is out of bounds", 10001)
        return aval_moves[number]

    @property
    @abc.abstractmethod
    def move_vector_size(self) -> int:
        return 0
