import sys


class Bot(object):
    def __init__(self):
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
        pass

    def update_state(self, player, type, value):
        pass

    def perform_action(self, type, time):
        pass

    def shutdown(self):
        self._should_shutdown = True
