import sys


class Bot(object):
    def __init__(self):
        self._should_shutdown = False

    def run(self):
        while not sys.stdin.closed and not self._should_shutdown:
            # Normalize input line
            input_line = sys.stdin.readline().rstrip().lower()

            if not len(input_line):
                continue

            if input_line.startswith('action'):
                pass
            elif input_line.startswith('quit'):
                self._should_shutdown = True
