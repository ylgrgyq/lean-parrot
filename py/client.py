"""
Hello
"""
import re
import json
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

WS_MANAGER = WebSocketManager()

class Client(WebSocketBaseClient):
    def __init__(self, addr, appid, peerid, router, serializer):
        super().__init__(addr)
        self.appid = appid
        self.peerid = peerid
        self._router = router
        self._serializer = serializer

    def handshake_ok(self):
        print("Handshake OK")
        WS_MANAGER.add(self)
        self._router.register_client(self)

    def opened(self):
        print("Socket opened")

    def serialize(self, msg):
        raise NotImplementedError

    def deserialize(self, msg):
        raise NotImplementedError

    def send(self, payload, binary=False):
        payload['appId'] = self.appid
        payload['peerId'] = self.peerid
        print("> ", payload)
        super().send(self._serializer.serialize(payload))

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
    def __init__(self, sub_protocol):
        self._appid = None
        self._peerid = None
        self._router = None
        self._addr = None
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
        return Client(self._addr, self._appid, self._peerid, self._router, serializer)

def client_builder(sub_protocol):
    return ClientBuilder(sub_protocol)

def start_wsman():
    WS_MANAGER.start()

def close_wsman():
    WS_MANAGER.close_all()
    WS_MANAGER.stop()
    WS_MANAGER.join()
