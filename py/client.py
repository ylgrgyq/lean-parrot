"""
webSocket Client
"""
import re
import json
import collections
from threading import Thread, Event

import colorama
from ws4py.client.threadedclient import WebSocketClient
from ws4py.websocket import Heartbeat
from ws4py.messaging import BinaryMessage

import util
import config
import commands

LOG = util.get_logger('client')

OPENED_CLIENTS = []


class Client(WebSocketClient):
    def __init__(self, addr, peer_id, ping_interval_secs, cmd_manager, serializer, protocol="lc.json.3"):
        super(Client, self).__init__(addr, protocols=[protocol])
        self._peer_id = peer_id
        self._serializer = serializer
        self._cmd_manager = cmd_manager
        if ping_interval_secs is None:
            self._ping_interval_secs = 60
        else:
            self._ping_interval_secs = ping_interval_secs
        self._expect_msgs_list = []
        self._matched_received = []
        self._heartbeat_job = Heartbeat(self, self._ping_interval_secs)
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._expect_msgs_list = []
        self._matched_received = []
        self._heartbeat_job.stop()
        super(Client, self).close()

    def handshake_ok(self):
        LOG.info(colorama.Fore.YELLOW + "Handshake OK")
        OPENED_CLIENTS.append(self)
        super().handshake_ok()

        if self._ping_interval_secs != 0:
            ping_thread = Thread(target=self._heartbeat_job.run)
            ping_thread.daemon = True
            ping_thread.start()

    def opened(self):
        LOG.info(colorama.Fore.YELLOW + "Socket opened")

    def send_msg(self, cmd_msg_args):
        if self._closed:
            raise RuntimeError(
                "Connection broken, please send msg after connected to server")

        msg = self._cmd_manager.complate_msg(cmd_msg_args)

        LOG.info("%s > %s" % (self._peer_id, json.dumps(msg)))

        msg = self._serializer.serialize(msg)
        if isinstance(msg, str):
            super().send(msg)
        else:
            super().send(BinaryMessage(bytes=msg))

    def send_msg_with_block_wait_resp(self, cmd_msg_args, resp=util.MATCH_ANY, timeout=15):
        if self._closed:
            raise RuntimeError(
                "Connection broken, please send msg after connected to server")

        e = Event()
        self._expect_msgs_list.insert(0, [resp, e])

        self.send_msg(cmd_msg_args)

        if not e.wait(timeout):
            raise Exception("Timeout on waiting for expect response")
        return self._matched_received.pop()

    def send_msg_with_expect_resps(self, cmd_msg_args, resps, timeout=15):
        if self._closed:
            raise RuntimeError(
                "Connection broken, please send msg after connected to server")

        events = []
        for c in resps:
            e = Event()
            self._expect_msgs_list.insert(0, [c, e])
            events.append(e)

        self.send_msg(cmd_msg_args)

        for e in events:
            if not e.wait(timeout):
                raise Exception("Timeout on waiting for expect response")
        received = self._matched_received
        self._matched_received = []
        return received

    def received_message(self, message):
        if isinstance(message, BinaryMessage):
            msg = self._serializer.deserialize(message.data)
        else:
            msg = self._serializer.deserialize(message)
        msg = self._cmd_manager.preprocess(msg)

        LOG.info(colorama.Fore.CYAN + "%s < %s" %
                 (self._peer_id, json.dumps(msg)))

        respond = self._cmd_manager.get_respond_msg(msg)
        if respond is not None:
            self.send_msg(respond)

        if self._expect_msgs_list:
            [expect_resp, e] = self._expect_msgs_list.pop()
            if util.partial_match_json(expect_resp, msg):
                self._matched_received.append(msg)
                e.set()
            else:
                LOG.info(colorama.Fore.MAGENTA +
                         "match failed expect %s, actual %s" % (expect_resp, msg))

    def add_expect_msgs(self, expect_msgs):
        events = []
        for m in expect_msgs:
            e = Event()
            self._expect_msgs_list.insert(0, [m, e])
            events.append(e)
        return ExpectMsgFuture(events)

    def closed(self, code, reason=None):
        self._closed = True
        LOG.info(colorama.Fore.YELLOW +
                 "WebSocket closed: %s %s" % (code, reason))


class ExpectMsgFuture:
    def __init__(self, events):
        assert len(events) != 0
        events.reverse()
        self._events = events

    def wait(self, timeout=5):
        assert len(self._events) != 0
        for e in self._events:
            if not e.wait(timeout):
                raise Exception("Timeout on waiting for expect response")


class ExpectMsgFutureCluster:
    def __init__(self, futures):
        assert len(futures) != 0
        self._futures = futures

    def wait(self, timeout=5):
        assert len(self._futures) != 0
        for f in self._futures:
            f.wait(timeout)


def add_expect_msgs_for_all(clients, expect_msgs):
    futures = []
    for c in clients:
        futures.append(c.add_expect_msgs(expect_msgs))
    return ExpectMsgFutureCluster(futures)


class JsonSerializer:
    def serialize(self, msg):
        return json.dumps(msg)

    def deserialize(self, msg):
        return json.loads(str(msg))


class ClientBuilder:
    def __init__(self):
        self._appid = None
        self._peerid = None
        self._addr = None
        self._ping_interval_secs = None
        self._protocol = config.DEFAULT_PROTOCOL

    def with_appid(self, appid):
        self._appid = appid
        return self

    def with_protocol(self, protocol):
        self._protocol = protocol
        return self

    def with_ping_interval_secs(self, interval_secs):
        self._ping_interval_secs = interval_secs
        return self

    def disable_ping(self):
        self._ping_interval_secs = 0
        return self

    def with_peerid(self, peerid):
        self._peerid = peerid
        return self

    def with_addr(self, addr):
        self._addr = addr
        return self

    def build(self):
        cmd_manager = commands.CommandsManager(
            self._appid, self._peerid)
        serializer = JsonSerializer()
        return Client(self._addr,
                      self._peerid,
                      self._ping_interval_secs,
                      cmd_manager,
                      serializer,
                      protocol=self._protocol)


def client_builder():
    return ClientBuilder()


def connect_to_ws_addr(client_id, addr):
    ws_client = client_builder() \
        .with_addr(addr) \
        .with_appid(config.APP_ID) \
        .with_peerid(client_id) \
        .build()
    LOG.info("%s connecting to %s" % (client_id, addr))
    ws_client.connect()
    return ws_client


def close_all_opened_clients():
    for c in OPENED_CLIENTS:
        c.close()
