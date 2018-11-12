"""
Global configs
"""
from configparser import ConfigParser

APP_KEY = None
APP_ID = None
APP_MASTER_KEY = None
ROUTER_URL = None
CLIENT_UA = None
DEFAULT_PROTOCOL = 'json.1'


def init_config(env):
    global APP_KEY
    global APP_ID
    global APP_MASTER_KEY
    global ROUTER_URL
    global CLIENT_UA

    cfg = ConfigParser()
    cfg.read('config.ini')

    APP_ID = cfg.get(env, "appid")
    APP_KEY = cfg.get(env, 'appkey')
    APP_MASTER_KEY = cfg.get(env, 'app_master_key')
    CLIENT_UA = cfg.get(env, 'ua', fallback='LeanParrot/1.0')
    app_group = cfg.get(env, 'app_group')
    if app_group == 'g0':
        ROUTER_URL = "https://%s.%s" % (APP_ID[0:8],
                                        cfg.get(env, 'im_router_addr_url_postfix'))
    else:
        ROUTER_URL = "https://router-%s-push.%s" % \
                     (app_group, cfg.get(env, 'im_router_addr_url_postfix'))
