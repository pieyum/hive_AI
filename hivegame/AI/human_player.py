from engine.hive import Hive
from AI.player import Player
from engine.hive_utils import Direction, HiveException
from utils import hexutil


class HumanPlayer(Player):
    def __init__(self, input_stream):
        self._input = input_stream

    def step(self, hive: 'Hive'):
        active_player = hive.current_player
        print(hive)
        print("pieces available: %s" % sorted(
            hive.level.get_unplayed_pieces(active_player)
        ))
        print("player %s play: " % active_player)

        # step out with return or exception
        while True:
            try:
                cmd = self._input.readline()
                # Do not accept empty lines
                while not cmd.strip():
                    cmd = self._input.readline()
                result = HumanPlayer.parse_cmd(cmd.strip(), hive)
                return result
            except KeyboardInterrupt:
                return None
            except (ValueError, HiveException):
                print("Invalid command")

    def feedback(self, succeeded) -> None:
        if succeeded:
            print()
            print("=" * 79)
            print()
        else:
            print("invalid play!")

    @staticmethod
    def parse_cmd(cmd, hive):
        if cmd == 'pass':
            return 'pass'
        if len(cmd) == 3:
            moving_piece = cmd
            target_cell = hexutil.origin
        else:
            if len(cmd) != 8:
                return ValueError("Failed to parse command")
            moving_piece = cmd[:3]
            point_of_contact = cmd[3:5]
            ref_piece_name = cmd[5:]
            direction = HumanPlayer.poc2direction(point_of_contact)
            target_cell = hive.poc2cell(ref_piece_name, direction)

        return hive.get_piece_by_name(moving_piece), target_cell

    @staticmethod
    def poc2direction(point_of_contact):
        """Parse point of contact to a Hive.direction"""""
        if point_of_contact == '|*':
            return Direction.HX_W
        if point_of_contact == '/*':
            return Direction.HX_NW
        if point_of_contact == '*\\':
            return Direction.HX_NE
        if point_of_contact == '*|':
            return Direction.HX_E
        if point_of_contact == '*/':
            return Direction.HX_SE
        if point_of_contact == '\\*':
            return Direction.HX_SW
        if point_of_contact == '=*':
            return Direction.HX_O
        raise ValueError('Invalid input for point of contact: "%s"' % point_of_contact)
