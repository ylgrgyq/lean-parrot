"""
Build command or parse command
"""
import time
import json
import hmac
import hashlib
from functools import wraps

import util
import config

def sign(sign_msg, k):
    return hmac.new(k.encode('utf-8'), sign_msg.encode('utf-8'), hashlib.sha1).digest().hex()

def add_sign(cmd_msg, convid=None, action=None, peerids=None):
    peerid = cmd_msg['peerId']
    ts = time.time()
    nonce = cmd_msg.get('nonce', util.generate_id())
    peerid = peerid if convid is None else ':'.join([peerid, convid])
    peerids = '' if peerids is None else ':'.join(sorted(peerids))
    sign_msg = ':'.join([config.APP_ID, peerid, peerids, str(ts), nonce])
    sign_msg = sign_msg if action is None else ':'.join([sign_msg, action])
    cmd_msg['t'] = ts
    cmd_msg['n'] = nonce
    cmd_msg['s'] = sign(sign_msg, config.APP_MASTER_KEY)
    return cmd_msg

def with_sign(cid_field_name = None, pids_field_name = None, action_name = None):
    def sign_decorator(fn):
        @wraps(fn)
        def wrap_sign(self, cmd_msg):
            [cid, pids] = map(cmd_msg.get, [cid_field_name, pids_field_name])
            cmd_msg = add_sign(cmd_msg, convid=cid, peerids=pids, action=action_name)
            return fn(self, cmd_msg)
        return wrap_sign
    return sign_decorator

class Command:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def process(self, router, msg):
        print("< ", json.dumps(msg))

    def build(self, cmd_msg):
        return cmd_msg

    def is_interactive_cmd(self):
        return True

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
        op_field = msg.get('op')
        if op_field is None or op_field not in self.sub_commands:
            super().process(router, msg)
        else:
            self.sub_commands[op_field].process(router, msg)

    def build(self, cmd_msg):
        op_field = cmd_msg.get('op')
        msg = None
        if op_field is None or self.sub_commands.get(op_field) is None:
            msg = cmd_msg
        else:
            msg = self.sub_commands[op_field].build(cmd_msg)
        msg['cmd'] = self.name
        return msg

class RegisteredCommands:
    def __init__(self):
        self._parents = list()
        self._childs = dict()

    def add_parent_cmd_cls(self, cmd_cls):
        self._parents.append(cmd_cls)

    def add_child_cmd_cls(self, parent_name, cmd_cls):
        childs = self._childs.get(parent_name, list())
        childs.append(cmd_cls)
        self._childs[parent_name] = childs

    def parent_cmd_cls_gen(self):
        for cmd_cls in self._parents:
            yield cmd_cls

    def child_cmd_cls_gen(self):
        for parent_name, cmd_cls in self._childs.items():
            yield [parent_name, cmd_cls]

COMMANDS = RegisteredCommands()

def register_command(parent_name = None):
    def wrapper(cls):
        if parent_name is None:
            COMMANDS.add_parent_cmd_cls(cls)
        else:
            COMMANDS.add_child_cmd_cls(parent_name, cls)
        return cls
    return wrapper

def init_commands():
    commands = dict()
    for parent_cls in COMMANDS.parent_cmd_cls_gen():
        cmd = parent_cls()
        commands[cmd.name] = cmd

    for parent_name, cmd_classes in COMMANDS.child_cmd_cls_gen():
        for cmd_cls in cmd_classes:
            cmd = cmd_cls()
            parent_cmd = commands[parent_name]
            parent_cmd.add(cmd)
    return commands

@register_command()
class DirectCommand(Command):
    _name = "direct"
    def __init__(self):
        super().__init__(DirectCommand._name)

@register_command()
class ConvCommand(CommandWithOp):
    _name = "conv"
    def __init__(self):
        super().__init__(ConvCommand._name)

@register_command(parent_name = "conv")
class ConvStartCommand(Command):
    _op_name = "start"
    def __init__(self):
        super().__init__(ConvStartCommand._op_name)

    @with_sign(pids_field_name='m')
    def build(self, cmd_msg):
        cmd_msg['unique'] = cmd_msg.get('unique', True)
        return cmd_msg

@register_command(parent_name = "conv")
class ConvAddCommand(Command):
    _op_name = "add"
    def __init__(self):
        super().__init__(ConvAddCommand._op_name)

    @with_sign(pids_field_name='m', cid_field_name='cid', action_name='invite')
    def build(self, cmd_msg):
        return cmd_msg

@register_command(parent_name = "conv")
class ConvRemoveCommand(Command):
    _op_name = "remove"
    def __init__(self):
        super().__init__(ConvRemoveCommand._op_name)

    @with_sign(pids_field_name='m', cid_field_name='cid', action_name='kick')
    def build(self, cmd_msg):
        return cmd_msg

@register_command()
class SessionCommand(CommandWithOp):
    _name = "session"
    def __init__(self):
        super().__init__(SessionCommand._name)

@register_command(parent_name = "session")
class SessionOpenCommand(Command):
    _op_name = "open"
    def __init__(self):
        super().__init__(SessionOpenCommand._op_name)

    @with_sign()
    def build(self, cmd_msg):
        cmd_msg['ua'] = cmd_msg.get('ua', config.CLIENT_UA)
        cmd_msg['configBitmap'] = 0xFFFF
        return cmd_msg

@register_command(parent_name = "session")
class SessionCloseCommand(Command):
    _op_name = "close"
    def __init__(self):
        super().__init__(SessionCloseCommand._op_name)

class CommandsManager:
    def __init__(self, appid, peerid):
        self.commands = init_commands()
        self._next_serial_id = 1
        self._appid = appid
        self._peerid = peerid

    def process(self, router, msg):
        cmd_in_msg = msg.get('cmd')
        if cmd_in_msg is not None:
            cmd = self.commands.get(cmd_in_msg)
            if cmd is None:
                print("< ", json.dumps(msg))
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
            cmd_msg['appId'] = self._appid
            cmd_msg['peerId'] = self._peerid
            msg = cmd_builder.build(cmd_msg)
            if cmd_builder.is_interactive_cmd():
                msg['i'] = self._next_serial_id
                self._next_serial_id += 1
            return msg
