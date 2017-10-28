import sys


class Cell(object):
    def __init__(self, x, y, owner_id, is_alive):
        self.x = x
        self.y = y
        self.owner_id = None
        self.is_alive = is_alive

    def __str__(self):
        state = 'alive' if self.is_alive else 'dead'

        return '<Cell({}, {}, {})>'.format(self.x, self.y, state)


class PlayerState(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.living_cells = None


class Bot(object):
    def __init__(self):
        self.id = None
        self.name = None

        self.opponent_id = None
        self.opponent_name = None
        self.players = None

        self.timebank = None
        self.time_per_move = None
        self.max_rounds = None
        self.round = None

        self.field_width = None
        self.field_height = None
        self.field = None

        self._should_shutdown = False
        self._command_registry = {
            'settings': self.update_settings,
            'update': self.update_state,
            'action': self.perform_action,
            'quit': self.shutdown,
        }

    def run(self):
        while not sys.stdin.closed and not self._should_shutdown:
            # Normalize input line
            input_line = sys.stdin.readline().rstrip().lower()

            if not len(input_line):
                continue

            input_data = input_line.split()
            input_type = input_data.pop(0)

            if input_type not in self._command_registry:
                sys.stderr.write('Invalid input type: {}\n'.format(input_type))

            command_func = self._command_registry[input_type]
            command_func(*input_data)

    def update_settings(self, key, value):
        if key == 'timebank':
            self.timebank = int(value)
        elif key == 'time_per_move':
            self.time_per_move = int(value)
        elif key == 'player_names':
            self.players = {}

            player_names = value.split(',')
            for name in player_names:
                player = PlayerState()
                player.name = name

                self.players[name] = player
        elif key == 'your_bot':
            self.name = value
        elif key == 'your_botid':
            self.id = value

            # TODO: Make more generic.
            self.opponent_id = '0' if self.id == '1' else '1'
        elif key == 'field_width':
            self.field_width = int(value)
        elif key == 'field_height':
            self.field_height = int(value)
        elif key == 'max_rounds':
            self.max_rounds = int(value)
        else:
            raise KeyError('Unknown key: {}'.format(key))

    def update_state(self, player, type, value):
        if player == 'game':
            if type == 'round':
                self.round = int(value)
            elif type == 'field':
                self.field = value
            else:
                raise KeyError('Unknown key: {}'.format(type))
        elif player in self.players:
            if type == 'living_cells':
                self.players[player].living_cells = int(value)
            else:
                raise KeyError('Unknown key: {}'.format(type))
        else:
            raise KeyError('Unknown player: {}'.format(player))

    def perform_action(self, type, time):
        pass

    def shutdown(self):
        self._should_shutdown = True

    def _parse_state(self, field):
        self.field = [[None] * self.field_width for _ in range(self.field_height)]

        for index, cell_owner in enumerate(field):
            column = index // self.field_width
            row = index % self.field_width

            cell_is_alive = cell_owner != '.'

            cell = Cell(column, row, cell_owner, cell_is_alive)

            self.field[row][column] = cell
