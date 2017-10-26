"""
Hello
"""
import time
import util
import config

class Command:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def process(self, router, msg):
        print("Known msg %s" % msg)

    def add(self, sub_command):
        raise NotImplementedError

    def remove(self, sub_command):
        raise NotImplementedError

    def build(self, cmd_args):
        raise NotImplementedError

class CommandWithOp(Command):
    def __init__(self, name):
        Command.__init__(self, name)
        self.sub_commands = dict()

    def add(self, sub_command):
        name = sub_command.name
        self.sub_commands[name] = sub_command

    def remove(self, sub_command):
        name = sub_command.name
        self.sub_commands.pop(sub_command.name, None)

    def process(self, router, msg):
        op = msg.get('op')
        if op is not None:
            self.sub_commands[op].process(router, msg)
        else:
            raise RuntimeError("Unknown op %s in command %s" % (op, self.name))

    def build(self, cmd_args):
        op = cmd_args.get('op')
        if op is None:
            raise RuntimeError("Need op for command %s in cmd_args %s" % (self.name, cmd_args))
        msg = self.sub_commands[op].build(cmd_args)
        msg['cmd'] = self.name
        return msg

class SessionCommand(CommandWithOp):
    _name = "session"
    def __init__(self):
        CommandWithOp.__init__(self, SessionCommand._name)

class SessionOpenCommand(Command):
    _op_name = "open"
    def __init__(self):
        Command.__init__(self, SessionOpenCommand._op_name)

    def build(self, cmd_args):
        msg = dict()
        msg['op'] = SessionOpenCommand._op_name
        msg['ua'] = cmd_args.get('ua', config.CLIENT_UA)
        peerid = cmd_args['peerId']
        msg['peerId'] = peerid
        nonce = cmd_args.get('nonce', util.generate_id())
        ts = time.time()
        signature = util.session_open_sign(peerid, ts, nonce)
        msg['t'] = ts
        msg['n'] = nonce
        msg['s'] = signature
        return msg

def register_session_commands():
    session_cmd = SessionCommand()

    sub_cmd = SessionOpenCommand()
    session_cmd.add(sub_cmd)

    return session_cmd

class CommandsGroup:
    def __init__(self):
        self.commands = dict()
        cmd = register_session_commands()
        self.commands[cmd.name] = cmd

    def process(self, router, msg):
        cmd_in_msg = msg.get['cmd']
        if cmd_in_msg is not None:
            cmd = self.commands[cmd_in_msg]
            cmd.process(router, msg)
        else:
            raise RuntimeError("Need 'cmd' in msg: %s" % msg)

    def build(self, cmd, cmd_args):
        cmd = self.commands[cmd]
        msg = cmd.build(cmd_args)
        return msg

