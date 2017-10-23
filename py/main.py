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
        self.cmdHandlerDict = dict()
        self._wsClient = None

    def register_command(self, cmd):
        self.cmdHandlerDict[cmd.command_name] = cmd

    def register_client(self, client):
        self._wsClient = client

    def dispatchUpstream(self, msg):
        handler = self.cmdHandlerDict.get(msg.get("cmd"))
        handler.process(self, msg)

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
        raise Exception("Get server failed")

if __name__ == "__main__":
    config.init_config()

    server_addr = get_servers(config.APP_ID, False)

    router = CommandRouter()
    commands.register_all_command(router)

    client.start_wsman()
    c = client.LeanParrotClient(server_addr, config.APP_ID, "2a", router)
    c.connect()

    try:
        command = input("Enter command in format 'command op k v':")
        # print("jkjkjk", command, re.split(r"\w+", command))
        # [command, *inputs] = re.split(r"\w+", command)
        print(command, "sdsd")

        # c.send({"cmd":"session", "peerId":"2a","appId":"","op":"open","ua":"py/test2"})
        # time.sleep(1)
        # c.close()
    except Exception as e:
        print("asdcjvkcjvkcjvkcv", e)

    print("asdfasdf")
    client.close_wsman()
