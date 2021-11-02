import sys
import time
import threading

class Spinner(threading.Thread):
    '''
    Context manager for a cursor-spinner.

    Have a message with a spinner display in the shell. When the context is
    exited, the spinner and initial message will be replaced by another message.

    Use:
        def some_method():
            for i in range(10):
                time.sleep(1)

        with Spinner('doing stuff', 'done!'):
            some_method()

    '''
    def __init__(self, busy_message, done_message):
        super().__init__(target=self._spin)
        self._stopevent = threading.Event()

        self.busy_message = busy_message
        self.done_message= done_message

    def stop(self):
        self._stopevent.set()

    def _spin(self):
        print(f'{self.busy_message} ', end='')

        while not self._stopevent.isSet():
            for t in '|/-\\':
                sys.stdout.write(t)
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

        # Clean up!
        sys.stdout.flush()
        sys.stdout.write('\x1b[1K\r')
        print(self.done_message)

WARN = '\033[93m'
EXIT = '\033[91m'
END = '\033[0m'

def warn(message, level=0):
    '''
    Prints a warning in yellow

    Params:
        message (str): The message.
        level (int): How far should the message be indented, each level equals two dashes.
    '''
    print(f'{WARN}{mess(message, level)}{END}')

def exit_with(exception=None, message='', level=0):
    '''
    Prints an exit message or the message of an exception and exits the program.
    '''
    send_mess = mess(exception, level) if exception else mess(message, level)
    print(f'{EXIT}{send_mess}{END}')

    sys.exit()

def get_level(level):
    return (level * '--' + ' ') if level else ''

def mess(message, level=0):
    return f'{get_level(level)}{message}'

