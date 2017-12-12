"""
Process starts here
"""
import json
import traceback
import readline
import argparse
import urllib3
import colorama

import commands
import client
import config
import input_parser

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
                        help="Which env in config.ini to use")
    parser.add_argument('--addr', default=None, dest="server_addr",
                        help="Server address connecting to")
    parser.add_argument('--secure', action="store_true", default=True, dest="is_secure_addr",
                        help="Use secure websocket addr")
    args = parser.parse_args()

    config.init_config(args.config_env)
    server_addr = args.server_addr
    if server_addr is None:
        server_addr = get_servers(config.APP_ID, args.is_secure_addr)
    print(colorama.Fore.YELLOW + "Connecting to %s" % server_addr)

    client.start_wsman()
    clt = client.client_builder(args.protocol) \
        .with_addr(server_addr) \
        .with_appid(config.APP_ID) \
        .with_peerid(args.peerid) \
        .build()
    clt.connect()

    while True:
        try:
            raw_str = input()
            if len(raw_str) != 0:
                cmd_msg_args = input_parser.parse_input_cmd_args(raw_str)
                clt.send_msg(cmd_msg_args)
            else:
                print(raw_str)
        except KeyboardInterrupt:
            break
        except Exception:
            print(colorama.Fore.RED + "Got exception: %s" % traceback.print_exc())

    clt.close()
    client.close_wsman()
    print(colorama.Fore.GREEN + "Client closed")

if __name__ == "__main__":
    colorama.init(autoreset=True)
    start_process()
