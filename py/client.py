"""
Hello
"""
import re
import json
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

WS_MANAGER = WebSocketManager()

class Client(WebSocketBaseClient):
    def __init__(self, addr, appid, peerid, router, cmd_manager, serializer):
        super().__init__(addr)
        self._appid = appid
        self._peerid = peerid
        self._router = router
        self._serializer = serializer
        self._cmd_manager = cmd_manager

    def handshake_ok(self):
        print("Handshake OK")
        WS_MANAGER.add(self)
        self._router.register_client(self)

    def opened(self):
        print("Socket opened")

    def send(self, cmd_msg_args):
        cmd_msg_args['appId'] = self._appid
        cmd_msg_args['peerId'] = self._peerid
        msg = self._cmd_manager.build(cmd_msg_args)
        print("> ", msg)
        super().send(self._serializer.serialize(msg))

    def received_message(self, message):
        self._router.dispatch_upstream(self._serializer.deserialize(message))

    def closed(self, code, reason=None):
        print("WebSocket closed", code, reason)

class JsonSerializer:
    def serialize(self, msg):
        return json.dumps(msg)

    def deserialize(self, msg):
        return json.loads(str(msg))

class ClientBuilder:
    def __init__(self, sub_protocol, cmd_manager):
        self._appid = None
        self._peerid = None
        self._router = None
        self._addr = None
        self._cmd_manager = cmd_manager
        self._sub_ptorocol = sub_protocol
        protos = re.split(r'\.', sub_protocol)
        self._protocol = protos[1]

    def with_appid(self, appid):
        self._appid = appid
        return self

    def with_router(self, router):
        self._router = router
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
        return Client(self._addr, self._appid, self._peerid, self._router,
                      self._cmd_manager, serializer)

def client_builder(sub_protocol, cmd_manager):
    return ClientBuilder(sub_protocol, cmd_manager)

def start_wsman():
    WS_MANAGER.start()

def close_wsman():
    WS_MANAGER.close_all()
    WS_MANAGER.stop()
    WS_MANAGER.join()
