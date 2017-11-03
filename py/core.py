"""
Hello
"""
import re
import json
import traceback
import readline
import urllib3
import argparse

import commands
import client
import config
import input_parser

class CommandRouter:
    def __init__(self):
        self._client = None
        self._commands_manager = None

    def register_commands_manager(self, manager):
        self._commands_manager = manager

    def register_client(self, clt):
        self._client = clt

    def dispatch_upstream(self, msg):
        self._commands_manager.process(self, msg)

    def send_downstream(self, msg):
        self._client.send(msg)

def get_servers(app_id, secure):
    """Get RTM server address"""
    router_addr = "%s?appId=%s" % (config.ROUTER_URL, app_id)
    router_addr = "%s&=secure=1" % router_addr if secure else router_addr
    http = urllib3.PoolManager()
    resp = http.request('GET', router_addr)
    if resp.status == 200:
        data = resp.data
        return json.loads(data)["server"]
    else:
        raise RuntimeError("Get server failed: %s" % resp)

def start_process():
    """Driver function to run this script"""
    parser = argparse.ArgumentParser(description="Command line client to comunicate with IM")
    parser.add_argument('--peerid', default='2a', dest="peerid", help="client peerId")
    parser.add_argument('--protocol', default='lc.json.3', dest="protocol", help="IM protocol code")
    parser.add_argument('--env', default='prod', dest="config_env",
                        help="Which config env to use")
    parser.add_argument('--secure', action="store_true", default=True, dest="is_secure_addr",
                        help="Use in secure websocket addr")
    args = parser.parse_args()

    config.init_config(args.config_env)
    server_addr = get_servers(config.APP_ID, args.is_secure_addr)
    print("Connecting to %s" % server_addr)

    router = CommandRouter()

    command_manager = commands.CommandsManager()
    router.register_commands_manager(command_manager)

    client.start_wsman()
    clt = client.client_builder(args.protocol, command_manager) \
        .with_addr(server_addr) \
        .with_appid(config.APP_ID) \
        .with_peerid(args.peerid) \
        .with_router(router) \
        .build()
    clt.connect()

    while True:
        # raw_str = input("Enter command in format 'op k v':")
        raw_str = input()
        try:
            cmd_msg_args = input_parser.parse_input_cmd_args(raw_str)
            clt.send(cmd_msg_args)
        except Exception:
            print("Got exception", traceback.print_exc())

    clt.close()
    client.close_wsman()
    print("Client closed")

if __name__ == "__main__":
    start_process()
