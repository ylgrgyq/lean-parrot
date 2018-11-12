"""
Process starts here
"""
import os
import atexit
import json
import traceback
import readline
import argparse
import colorama
import requests
from requests.adapters import HTTPAdapter

import commands
import client
import config
import input_parser
import util

LOG = util.get_logger('core')


def get_servers(secure=True):
    payload = {'appId': config.APP_ID, 'secure': secure}

    auth_url = config.ROUTER_URL
    if not auth_url.startswith("http"):
        auth_url = "https://" + auth_url

    with requests.Session() as session:
        session.mount(auth_url, HTTPAdapter(max_retries=3))
        resp = session.get(auth_url, params=payload, timeout=1)
        LOG.info("get router link got response %s" % resp.json())
        return resp.json()["server"]


def start_process():
    """Driver function to run this script"""
    parser = argparse.ArgumentParser(
        description="Command line client to comunicate with IM")
    parser.add_argument('--peerid', default='2a',
                        dest="peerid", help="client peerId")
    parser.add_argument('--protocol', default='lc.json.3',
                        dest="protocol", help="IM protocol code")
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
        server_addr = get_servers(args.is_secure_addr)
    print(colorama.Fore.YELLOW + "Connecting to %s" % server_addr)

    clt = client.client_builder() \
        .with_addr(server_addr) \
        .with_appid(config.APP_ID) \
        .with_protocol(args.protocol) \
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
            print(colorama.Fore.RED + "Got exception: %s" %
                  traceback.print_exc())

    clt.close()
    client.close_all_opened_clients()
    print(colorama.Fore.GREEN + "Client closed")


def prepare_history_file():
    # copied from https://docs.python.org/3/library/readline.html
    histfile = os.path.join(
        os.path.expanduser("~"), ".game_command_line_testing_tool_history")
    try:
        readline.read_history_file(histfile)
        # default history len is -1 (infinite), which may grow unruly
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)


if __name__ == "__main__":
    prepare_history_file()
    colorama.init(autoreset=True)
    start_process()
