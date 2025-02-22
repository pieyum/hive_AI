from __future__ import annotations
import engine.environment.aienvironment as ai_env

from utils.game_state import GameState
from utils import hexutil

from pieces.piece import HivePiece

from engine.hive_utils import Player, HiveException, Direction
from utils.ascii_view import HiveView

import engine.hive_validation as valid
import pieces.piece_factory as piece_fact

import logging

from typing import List, Tuple, Any


class Hive(object):
    """
    The Hive Game.
    This class enforces the game rules.
    """

    def __init__(self):
        self.level = GameState()

    def reset(self) -> None:
        """
        Prepare the game to be played
        """
        self.level = GameState()

    @property
    def current_player(self) -> Player:
        """
        :return: The current player
        """
        return self.level.current_player

    def get_piece_by_name(self, piece_name: str) -> HivePiece:
        """
        :param piece_name: 3 digit name of piece. E.g. wQ1
        :return: The piece object
        """
        return piece_fact.name_to_piece(piece_name)


    def locate(self, piece_name: str) -> hexutil.Hex:
        """
        Returns the cell where the piece is positioned.
        piece_name is a piece identifier (string)
        """
        p = piece_fact.name_to_piece(piece_name)
        return self.level.find_piece_position(p)

    @staticmethod
    def _toggle_player(player: Player):
        return Player.BLACK if player == Player.WHITE else Player.WHITE

    def action_piece_to(self, piece: HivePiece, target_cell: hexutil.Hex):
        """
        Performs an action with the given piece to the given target cell.
        If the place is already on board it means a movement. Otherwise it
        means a piece placement.
        """
        pos = self.locate(piece)
        if not pos:
            self._place_piece_to(piece, target_cell)
        else:
            self._move_piece_to(piece, pos, target_cell)
        self.level.current_player = self._toggle_player(self.level.current_player)

    def validate_action(self, piece: HivePiece, target_cell: hexutil.Hex) -> bool:
        pos = self.locate(piece)

        # TODO move queen rules outside of function
        if not valid.validate_turn(self, pos, piece):
            logging.info("Turn fault")
            return False

        # movement
        if pos:
            if not valid.validate_move_piece(self, piece, pos, target_cell):
                logging.info("Invalid piece placement")
                return False
        else:
            if not valid.validate_place_piece(self, piece, target_cell):
                logging.info("Invalid piece placement")
                return False
        return True

    def _move_piece_to(self, piece: HivePiece, pos:hexutil.Hex, target_cell: hexutil.Hex) -> None:
        """
        Moves the given piece to the target cell.
        It does start a complete action, since it does
        not increment the turn value.
        """
        assert pos
        # is the move valid
        if not valid.validate_turn(self, pos, piece):
            raise HiveException("Invalid Piece Movement", 10002)

        if not valid.validate_move_piece(self, piece, pos, target_cell):
            raise HiveException("Invalid Piece Movement", 10002)

        # Update piece and map
        self.level.move_to(piece, pos, target_cell)

    def move_piece_without_action(self, piece_name: str, ref_piece_name: str, ref_direction: Direction) -> None:
        """
        Performs a step without action. It means the current player remains. Useful for testing or for console input.
        :param piece_name: The name of the piece to move
        :param ref_piece_name: The name of the piece the bug should be placed next to
        :param ref_direction: The direction which side of the referenced piece the piece should move to.
        """

        target_cell = self.poc2cell(ref_piece_name, ref_direction)
        piece = self.get_piece_by_name(piece_name)
        piece_pos = self.level.find_piece_position(piece)
        if not piece_pos:
            raise HiveException("Cannot move piece which is not on board", 9996)
        self._move_piece_to(piece, piece_pos, target_cell)

    def _place_piece_to(self, piece: HivePiece, to_cell: hexutil.Hex) -> None:
        """
        Places a piece to the given target cell.
        It does start a complete action, since it does
        not increment the turn value.
        """

        # is the placement valid
        if not valid.validate_turn(self, None, piece):
            raise HiveException("Invalid Piece Placement", 10003)

        if not valid.validate_place_piece(self, piece, to_cell):
            logging.info("Invalid piece placement")
            raise HiveException("Invalid Piece Placement", 10003)

        self.level.append_to(piece, to_cell)

    def place_piece_without_action(self, piece_name: str, ref_piece_name: str = None, ref_direction: Direction = None)\
            -> None:
        """
        Place a piece on the playing board without performing an action.
        :param piece_name: The name of the piece to place
        :param ref_piece_name: The name of the piece the bug should be placed next to
        :param ref_direction: The direction which side of the referenced piece the piece should be placed to.
        """

        # if it's the first piece, we put it to cell (0, 0)
        if ref_piece_name is None:
            target_cell = hexutil.origin
        else:
            target_cell = self.poc2cell(ref_piece_name, ref_direction)
        piece = self.get_piece_by_name(piece_name)
        return self._place_piece_to(piece, target_cell)



    def poc2cell(self, ref_piece: str, point_of_contract: Direction) -> hexutil.Hex:
        """
        Translates a relative position (piece, point of contact) into
        a hexagon
        """
        assert point_of_contract < 9
        ref_cell = self.locate(ref_piece)
        if not ref_cell:
            logging.error("Cannot find piece by name: {}".format(ref_piece))
            logging.debug(self)
            error_msg = "Cannot locate reference piece by name"
            raise HiveException(error_msg, 9996)

        if point_of_contract > 6:
            return ref_cell  # above or below
        return self.level.goto_direction(ref_cell, point_of_contract)

    def bee_moves(self, cell: hexutil.Hex) -> List[hexutil.Hex]:
        """
        A bee can move to an adjacent target position only if:
        - target position is free
        - and there is a piece adjacent to both the bee and that position
        - and there is a free cell that is adjacent to both the bee and the
          target position.
        :param cell: The hexagon the queen is currently at.
        :return: A list of hexagons where the queen can possibly go
        """
        available_hexes = []
        surroundings = cell.neighbours()
        for nb in surroundings:
            if not self.level.is_cell_free(nb):
                continue
            # does it have an adjacent free and an adjacent occupied cell that
            # is also adjacent to the starting cell
            mutual_nbs = list(GameState.get_mutual_neighbors(cell, nb))
            assert len(mutual_nbs) == 2  # there are always two of them
            if self.level.is_cell_free(mutual_nbs[0]) != self.level.is_cell_free(mutual_nbs[1]):
                available_hexes.append(nb)

        return available_hexes

    @staticmethod
    def _decode_action_number(action_number: int, player: Player) -> Tuple[str, Any]:
        # initial
        pieces = piece_fact.sorted_piece_list(player)
        pc = len(pieces)
        if action_number < pc - 1:
            pieces = [p for p in pieces if p.kind != 'Q']
            return 'init', pieces[action_number]
        action_number -= pc - 1

        # piece placement
        place_bound = pc * (pc - 1) * 6
        if action_number < place_bound:
            one_bug_bound = (pc - 1) * 6
            action_type = action_number % one_bug_bound
            piece_number = action_number // one_bug_bound
            adj_piece_number = action_type // 6
            direction = (action_type % 6) + 1 # starting from west, clockwise
            piece = pieces[piece_number]
            adj_piece = [p for p in pieces if p != piece][adj_piece_number]
            return 'place', (piece, adj_piece, direction)
        action_number -= place_bound

        # movement
        for piece in pieces:
            assert action_number >= 0
            # Find piece
            if action_number - piece.move_vector_size >= 0:
                action_number -= piece.move_vector_size
                continue
            return 'move', (piece, action_number)

        # Index overflow
        error_msg = "Invalid action number, out of bounds"
        logging.error(error_msg)
        raise HiveException(error_msg, 10010)

    def action_from_vector(self, action_number: int) -> (Tuple[HivePiece, hexutil.Hex]):
        """
        Maps an action number to an actual action. The fixed size action space is explained
        in detail at :func:`.hive_representation.get_all_action_vector``
        :param action_number:  index of the action from the fixed size action space.
        :return: A tuple of (piece, end_cell), where piece is the piece on which the action
        is executed. end_cell is the target location of the action.
        """
        assert action_number >= 0
        atype, decoded = Hive._decode_action_number(action_number, self.level.current_player)
        if atype == 'init':
            # That's an initial movement
            if len(self.level.get_played_pieces()) >= 2:
                error_msg = "Invalid action number, it should not be an initial movement"
                logging.error(error_msg)
                raise HiveException(error_msg, 10006)
            # remove queen piece
            if self.level.get_tile_content(hexutil.origin):
                # It's symmetric, so just pick the first neighbor
                return decoded, hexutil.origin.neighbours()[0]
            else:
                return decoded, hexutil.origin
        elif atype == 'place':
            (piece, adj_piece, direction) = decoded
            # piece should not be placed yet.
            if self.level.find_piece_position(piece):
                error_msg = "Attempt to place piece which is already placed"
                logging.error(error_msg)
                logging.error("piece: {}, adjacent piece: {}, direction: {}, action number: {}".format(
                    piece, adj_piece, direction, action_number))
                raise HiveException(error_msg, 10010)
            # Find adjacent piece on board
            adj_pos = self.level.find_piece_position(adj_piece)
            if adj_pos is None:
                error_msg = "Invalid action number, trying to place piece next to an unplayed piece"
                logging.error(error_msg)
                logging.error("piece: {}, adjacent piece: {}, direction: {}, action number: {}".format(
                    piece, adj_piece, direction, action_number))
                logging.error("played pieces: {}".format(self.level.get_played_pieces(None)))
                state = ai_env.ai_environment.get_init_board()
                current_player=1
                canonical_board = ai_env.ai_environment.get_canonical_form(state, current_player)
                logging.error("move validity: {}".format(ai_env.ai_environment.get_valid_moves(canonical_board, current_player)[action_number]))
                raise HiveException(error_msg, 10008)
            target_cell = self.level.goto_direction(adj_pos, direction)
            return piece, target_cell
        elif atype == 'move':
            (piece, inner_action) = decoded
            pos = self.level.find_piece_position(piece)
            if not pos:
                # It should be placed if we want to move it
                error_msg = "Invalid action number, trying to move a piece which is not yet placed"
                logging.error(error_msg)
                raise HiveException(error_msg, 10009)
            return piece, piece.index_to_target_cell(self, inner_action, pos)

        # Index overflow
        error_msg = "Invalid action"
        logging.error(error_msg)
        raise HiveException(error_msg, 10010)

    def _piece_from_piece_set(self, index:int, excep: HivePiece=None) -> HivePiece:
        """
        :param index: Index of bug from the piece set given by factory
        :param excep: Exception bug. It is omitted from the list.
        :return: hive peace according to the index number.
        """
        pieces = piece_fact.sorted_piece_list(self.level.current_player)
        if excep:
            pieces.remove(excep)
        return pieces[index]

    @staticmethod
    def _get_piece_names_on_board(adjacency):
        result = []
        for (piece_name, row) in adjacency.items():
            if all([cell == 0 for cell in row.values()]):
                continue  # not played, nothing to do here
            result.append(piece_name)
        return result

    def __str__(self):
        return HiveView(self.level).__str__()
