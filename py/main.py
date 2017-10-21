"""
Hello
"""
import time
import commands
import client
import fileinput
import re

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

if __name__ == "__main__":


    router = CommandRouter()
    commands.register_all_command(router)

    client.start_wsman()
    c = client.LeanParrotClient(addr, router)
    c.connect()

    try:
        print("Enter next command in format 'command op k v':")
        for line in fileinput.input():
            inputs = re.split("\w+")

            print(inputs)
        c.send({"cmd":"session", "peerId":"2a","appId":"","op":"open","ua":"py/test2"})
        time.sleep(1)
        c.close()
    except Exception as e:
        print("asdcjvkcjvkcjvkcv", e)

    print("asdfasdf")
    client.close_wsman()
