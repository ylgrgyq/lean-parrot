"""
Hello
"""
import time

import hmac
import hashlib

import util
import config

class SignatureMixin:
    def sign(self, sign_msg, k):
        return hmac.new(k.encode('utf-8'), sign_msg.encode('utf-8'), hashlib.sha1).digest().hex()

    def add_sign(self, cmd_msg, convid=None, action=None, peerids=None):
        peerid = cmd_msg['peerId']
        ts = time.time()
        nonce = cmd_msg.get('nonce', util.generate_id())
        peerid = peerid if convid is None else ':'.join([peerid, convid])
        peerids = '' if peerids is None else ':'.join(sorted(peerids))
        sign_msg = ':'.join([config.APP_ID, peerid, peerids, str(ts), nonce])
        sign_msg = sign_msg if action is None else ':'.join([sign_msg, action])
        cmd_msg['t'] = ts
        cmd_msg['n'] = nonce
        cmd_msg['s'] = self.sign(sign_msg, config.APP_MASTER_KEY)
        return cmd_msg

class Command:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def process(self, router, msg):
        print("< ", msg)

    def add(self, sub_command):
        raise NotImplementedError

    def remove(self, sub_command):
        raise NotImplementedError

    def build(self, cmd_msg):
        return cmd_msg

class CommandWithOp(Command):
    def __init__(self, name):
        Command.__init__(self, name)
        self.sub_commands = dict()

    def add(self, sub_command):
        name = sub_command.name
        self.sub_commands[name] = sub_command

    def remove(self, sub_command):
        self.sub_commands.pop(sub_command.name, None)

    def process(self, router, msg):
        op = msg.get('op')
        if op is None or op not in self.sub_commands:
            super().process(router, msg)
        else:
            self.sub_commands[op].process(router, msg)

    def build(self, cmd_msg):
        op = cmd_msg.get('op')
        msg = None
        if op is None:
            msg = cmd_msg
        else:
            msg = self.sub_commands[op].build(cmd_msg)
        msg['cmd'] = self.name
        return msg

class DirectCommand(Command):
    _name = "direct"
    def __init__(self):
        super().__init__(DirectCommand._name)

class ConvCommand(CommandWithOp):
    _name = "conv"
    def __init__(self):
        super().__init__(ConvCommand._name)

class ConvStartCommand(Command, SignatureMixin):
    _op_name = "start"
    def __init__(self):
        super().__init__(ConvStartCommand._op_name)
    def build(self, cmd_msg):
        members = cmd_msg['m']
        cmd_msg['unique'] = cmd_msg.get('unique', True)
        return self.add_sign(cmd_msg, peerids=members)

class ConvAddCommand(Command, SignatureMixin):
    _op_name = "add"
    def __init__(self):
        super().__init__(ConvAddCommand._op_name)
    def build(self, cmd_msg):
        cid = cmd_msg['cid']
        members = cmd_msg['m']
        return self.add_sign(cmd_msg, convid=cid, peerids=members)

class ConvRemoveCommand(Command, SignatureMixin):
    _op_name = "remove"
    def __init__(self):
        super().__init__(ConvRemoveCommand._op_name)
    def build(self, cmd_msg):
        cid = cmd_msg['cid']
        members = cmd_msg['m']
        return self.add_sign(cmd_msg, convid=cid, peerids=members)

class SessionCommand(CommandWithOp):
    _name = "session"
    def __init__(self):
        super().__init__(SessionCommand._name)

class SessionOpenCommand(Command, SignatureMixin):
    _op_name = "open"
    def __init__(self):
        super().__init__(SessionOpenCommand._op_name)

    def build(self, cmd_msg):
        cmd_msg = self.add_sign(cmd_msg)
        cmd_msg['ua'] = cmd_msg.get('ua', config.CLIENT_UA)
        return cmd_msg

class SessionCloseCommand(Command):
    _op_name = "close"
    def __init__(self):
        super().__init__(SessionCloseCommand._op_name)

def register_session_commands():
    session_cmd = SessionCommand()
    session_cmd.add(SessionOpenCommand())
    session_cmd.add(SessionCloseCommand())

    return session_cmd

def register_conv_commands():
    session_cmd = ConvCommand()
    session_cmd.add(ConvStartCommand())

    return session_cmd

class CommandsManager:
    def __init__(self):
        cmd = register_session_commands()
        self.commands = {cmd.name: cmd}
        cmd = register_conv_commands()
        self.commands[cmd.name] = cmd

    def process(self, router, msg):
        cmd_in_msg = msg.get('cmd')
        if cmd_in_msg is not None:
            cmd = self.commands.get(cmd_in_msg)
            if cmd is None:
                print("< ", msg)
            else:
                cmd.process(router, msg)
        else:
            raise RuntimeError("Receive msg without 'cmd': %s" % msg)

    def build(self, cmd_msg):
        cmd = cmd_msg['cmd']
        cmd_builder = self.commands.get(cmd)
        if cmd_builder is None:
            cmd_msg['cmd'] = cmd
            return cmd_msg
        else:
            return cmd_builder.build(cmd_msg)
