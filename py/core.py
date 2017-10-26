"""
Hello
"""
import re
import json
import traceback
import urllib3

import commands
import client
import config

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
    config.init_config('prod')
    server_addr = get_servers(config.APP_ID, False)

    router = CommandRouter()

    client.start_wsman()
    clt = client.client_builder("lc.json.3") \
        .with_addr(server_addr) \
        .with_appid(config.APP_ID) \
        .with_peerid("2a") \
        .with_router(router) \
        .build()
    clt.connect()

    command_manager = commands.CommandsManager()
    router.register_commands_manager(command_manager)

    while True:
        raw_str = input("Enter command in format 'command op k v':")
        [command, cmd, *args] = re.split(r"\s+", raw_str)
        if command != 'quit':
            try:
                i = iter(args)
                cmd_msg = dict(zip(i, i))
                msg = command_manager.build(cmd, cmd_msg)
                clt.send(msg)
            except Exception as exc:
                print("Got exception", traceback.print_exc())
        else:
            break

    clt.close()
    client.close_wsman()
    print("Client closed")

if __name__ == "__main__":
    start_process()
