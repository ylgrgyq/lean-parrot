"""
Hello
"""

import json
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

wsman = WebSocketManager()

class LeanParrotClient(WebSocketBaseClient):
    def __init__(self, addr, router):

        WebSocketBaseClient.__init__(self, addr)
        self._router = router

    def handshake_ok(self):
        print("Handshake OK")
        wsman.add(self)
        self._router.register_client(self)

    def opened(self):
        print("Socket opened")

    def send(self, m):
        WebSocketBaseClient.send(self, json.dumps(m))

    def received_message(self, m):
        print("Received msg", m)
        self._router.dispatchUpstream(json.loads(str(m)))

    def closed(self, status, reason):
        print("WebSocket closed", status, reason)

def start_wsman():
    wsman.start()

def close_wsman():
    wsman.close_all()
    wsman.stop()
    wsman.join()
