import random
import sys

from collections import Counter


class Cell(object):
    def __init__(self, x, y, owner_id, is_alive):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.is_alive = is_alive
        self.neighbors = []

        self._next_state = None

    def add_neighbor(self, cell):
        if cell not in self.neighbors:
            self.neighbors.append(cell)
            cell.add_neighbor(self)

    def get_next_state_owner_id(self):
        if self.get_next_state() == 'alive':
            owner_counts = Counter()
            for n in self.get_alive_neighbors():
                owner_counts[n.owner_id] += 1

            # Gets the zeroth index of the zeroth item of the 1-sized list.
            return owner_counts.most_common(1)[0][0]

        return None

    def get_rebirthing_neighbors(self):
        return [n for n in self.neighbors if n.get_next_state() == 'alive']

    def get_alive_neighbors(self):
        return [n for n in self.neighbors if n.is_alive]

    def get_dead_neighbors(self):
        return [n for n in self.neighbors if not n.is_alive]

    def get_next_state(self):
        if not self._next_state:
            alive_neighbors = len([n for n in self.neighbors if n.is_alive])

            if self.is_alive:
                self._next_state = 'alive' if alive_neighbors in [2, 3] else 'dead'
            else:
                self._next_state = 'alive' if alive_neighbors == 3 else 'dead'

        return self._next_state

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
                self._parse_state(value.split(','))
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
        self.timebank += time
        if type == 'move':
            self._do_move()
        else:
            raise KeyError('Unknown action type: {}'.format(type))

    def shutdown(self):
        self._should_shutdown = True

    def _parse_state(self, field):
        self.field = [[None] * self.field_width for _ in range(self.field_height)]

        for index, cell_owner in enumerate(field):
            column = index % self.field_width
            row = index // self.field_width

            cell_is_alive = cell_owner != '.'

            cell = Cell(column, row, cell_owner, cell_is_alive)

            # Add neighbors
            possible_neighbors = [
                (row - 1, column - 1),
                (row - 1, column),
                (row - 1, column + 1),
                (row, column - 1),
            ]

            self.field[row][column] = cell

            for n in possible_neighbors:
                if n[0] < 0:
                    continue

                if n[1] < 0 or n[1] >= self.field_width:
                    continue

                neighbor = self.field[n[0]][n[1]]
                cell.add_neighbor(neighbor)

    def _do_move(self):
        my_dying_cells = []
        opponent_living_cells = []

        for row in self.field:
            for cell in row:
                if cell.owner_id == self.id and cell.get_next_state() == 'dead':
                    my_dying_cells.append(cell)
                if cell.owner_id == self.opponent_id and cell.get_next_state() == 'alive':
                    opponent_living_cells.append(cell)

        if len(my_dying_cells) >= 2:
            spawn_counts = {}
            for cell in my_dying_cells:
                opponent_spawn_count = len([c for c in cell.get_rebirthing_neighbors()
                                            if c.get_next_state_owner_id() == self.opponent_id])
                own_spawn_count = len([c for c in cell.get_rebirthing_neighbors()
                                       if c.get_next_state_owner_id() == self.id])

                spawn_counts[cell] = (opponent_spawn_count, own_spawn_count)

            cells_to_sacrifice = sorted(spawn_counts.items(), key=lambda x: (x[1][0], x[1][1]))
            cells_to_sacrifice = cells_to_sacrifice[:2]

            my_dying_cells = [c for c in my_dying_cells if c not in cells_to_sacrifice]
            my_savable_cells = [c for c in my_dying_cells if c.get_alive_neighbors() == 2]
            opponent_killable_cells = [c for c in opponent_living_cells
                                       if c.get_alive_neighbors() == 3]

            if my_savable_cells:
                cell_save_count = Counter()

                for cell in my_savable_cells:
                    for save_cell in cell.get_dead_neighbors():
                        cell_save_count[save_cell] += 1

                save_cell = cell_save_count.most_common(1)[0][0]

                sys.stdout.write('birth {},{} {},{} {},{}\n'.format(
                    save_cell.x, save_cell.y,
                    cells_to_sacrifice[0].x, cells_to_sacrifice[0].y,
                    cells_to_sacrifice[1].x, cells_to_sacrifice[1].y,
                ))
            elif opponent_killable_cells:
                cell_kill_count = Counter()

                for cell in opponent_killable_cells:
                    for kill_cell in cell.get_dead_neighbors():
                        cell_kill_count[kill_cell] += 1

                kill_spot = cell_kill_count.most_common(1)[0][0]

                sys.stdout.write('birth {},{} {},{} {},{}\n'.format(
                    kill_spot.x, kill_spot.y,
                    cells_to_sacrifice[0].x, cells_to_sacrifice[0].y,
                    cells_to_sacrifice[1].x, cells_to_sacrifice[1].y,
                ))
            else:
                self._kill_opponent_cell(opponent_living_cells)
        else:
            self._kill_opponent_cell(opponent_living_cells)
        sys.stdout.flush()

    @staticmethod
    def _kill_opponent_cell(opponent_cells):
        if opponent_cells:
            spawn_count = Counter()
            for cell in opponent_cells:
                spawn_count[cell] += len([c for c in cell.get_rebirthing_neighbors()
                                          if c.get_next_state_owner_id() == opponent_cells])

            cell_to_kill = spawn_count.most_common(1)[0][0]
            sys.stdout.write('kill {},{}\n'.format(cell_to_kill.x, cell_to_kill.y))
        else:
            sys.stdout.write('no_moves\n')
