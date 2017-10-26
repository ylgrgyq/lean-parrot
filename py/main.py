"""
Hello
"""
import time
import fileinput
import re
import urllib3
import commands
import client
import config
import json

class CommandRouter:
    def __init__(self):
        self._wsClient = None
        self.command_group = None

    def register_command_group(self, command_group):
        self.command_group = command_group

    def register_client(self, client):
        self._wsClient = client

    def dispatchUpstream(self, msg):
        self.command_group.process(self, msg)

    def sendDownstream(self, msg):
        self._wsClient.send(msg)

def get_servers(app_id, secure):
    router_addr = "%s?appId=%s" % (config.ROUTER_URL, app_id)
    router_addr = "%s&=secure=1" % router_addr if secure else router_addr
    http = urllib3.PoolManager()
    resp = http.request('GET', router_addr)
    if resp.status == 200:
        data = resp.data
        return json.loads(data)["server"]
    else:
        raise RuntimeError("Get server failed")

if __name__ == "__main__":
    config.init_config()

    server_addr = get_servers(config.APP_ID, False)

    router = CommandRouter()

    client.start_wsman()
    c = client.client_builder("lc.json.3") \
        .with_addr(server_addr) \
        .with_appid(config.APP_ID) \
        .with_peerid("2a") \
        .with_router(router) \
        .build()
    c.connect()

    commands_group = commands.CommandsGroup()
    router.register_command_group(commands_group)

    try:
        command = input("Enter command in format 'command op k v':")
        [command, rtm_cmd, *args] = re.split(r"\s+", command)
        if command != 'quit':
            i = iter(args)
            rtm_body = dict(zip(i, i))
            msg = commands_group.build(rtm_cmd, rtm_body)
            c.send(msg)
        else:
            # c.send({"cmd":"session", "peerId":"2a","appId":"","op":"open","ua":"py/test2"})
            time.sleep(1)
            c.close()
    except Exception as e:
        print("Got exception", e)

    time.sleep(1)
    print("I'm closing")
    c.close()
    client.close_wsman()
