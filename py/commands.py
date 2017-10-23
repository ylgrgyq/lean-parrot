"""
Hello
"""

class AbstractCommand:
    def __init__(self, name):
        self._command_name = name

    @property
    def command_name(self):
        return self._command_name

    def process(self, router, msg):
        print("Known msg %s" % msg)

class SessionCommand(AbstractCommand):
    def __init__(self):
        self._name = "session"
        AbstractCommand.__init__(self, self._name)

def register_all_command(router):
    router.register_command(SessionCommand())

