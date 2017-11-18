"""
webSocket Client
"""
import re
import json
import commands
import colorama
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

WS_MANAGER = WebSocketManager()

class Client(WebSocketBaseClient):
    def __init__(self, addr, appid, peerid, serializer):
        super().__init__(addr, heartbeat_freq=5.0)
        self._serializer = serializer
        self._cmd_manager = commands.CommandsManager(appid, peerid)

    def handshake_ok(self):
        print(colorama.Fore.YELLOW + "Handshake OK")
        WS_MANAGER.add(self)

    def opened(self):
        print(colorama.Fore.YELLOW + "Socket opened")

    def send_msg(self, cmd_msg_args):
        msg = self._cmd_manager.build(cmd_msg_args)
        print("> ", json.dumps(msg))
        super().send(self._serializer.serialize(msg))

    def received_message(self, message):
        self._cmd_manager.process(self, self._serializer.deserialize(message))

    def closed(self, code, reason=None):
        print(colorama.Fore.YELLOW + "WebSocket closed: %s %s" % (code, reason))

class JsonSerializer:
    def serialize(self, msg):
        return json.dumps(msg)

    def deserialize(self, msg):
        return json.loads(str(msg))

class ClientBuilder:
    def __init__(self, sub_protocol):
        self._appid = None
        self._peerid = None
        self._addr = None
        self._sub_ptorocol = sub_protocol
        protos = re.split(r'\.', sub_protocol)
        self._protocol = protos[1]

    def with_appid(self, appid):
        self._appid = appid
        return self

    def with_peerid(self, peerid):
        self._peerid = peerid
        return self

    def with_addr(self, addr):
        self._addr = addr
        return self

    def build(self):
        serializer = JsonSerializer()
        if self._protocol == 'json':
            serializer = JsonSerializer()
        return Client(self._addr, self._appid, self._peerid, serializer)

def client_builder(sub_protocol):
    return ClientBuilder(sub_protocol)

def start_wsman():
    WS_MANAGER.start()

def close_wsman():
    WS_MANAGER.close_all()
    WS_MANAGER.stop()
    WS_MANAGER.join()
