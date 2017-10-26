"""
Hello
"""
import re
import json
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

wsman = WebSocketManager()

class Client(WebSocketBaseClient):
    def __init__(self, addr, appid, peerid, router, serializer):
        WebSocketBaseClient.__init__(self, addr)
        self.appid = appid
        self.peerid = peerid
        self._router = router
        self._serializer = serializer

    def handshake_ok(self):
        print("Handshake OK")
        wsman.add(self)
        self._router.register_client(self)

    def opened(self):
        print("Socket opened")

    def serialize(self, m):
        raise NotImplementedError

    def deserialize(self, m):
        raise NotImplementedError

    def send(self, m):
        m['appId'] = self.appid
        m['peerId'] = self.peerid
        WebSocketBaseClient.send(self, self._serializer.serialize(m))

    def received_message(self, m):
        print("Received msg", m)
        self._router.dispatchUpstream(self._serializer.deserialize(m))

    def closed(self, status, reason):
        print("WebSocket closed", status, reason)

class JsonSerializer:
    def serialize(self, m):
        return json.dumps(m)

    def deserialize(self, m):
        return json.loads(str(m))

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
        serializer = None
        if self._protocol == 'json':
            serializer = JsonSerializer()
        else:
            serializer = JsonSerializer()
        return Client(self._addr, self._appid, self._peerid, self._router, JsonSerializer())

def client_builder(sub_protocol):
    return ClientBuilder(sub_protocol)

def start_wsman():
    wsman.start()

def close_wsman():
    wsman.close_all()
    wsman.stop()
    wsman.join()
