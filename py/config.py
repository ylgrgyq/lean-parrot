from configparser import ConfigParser

APP_KEY = None
APP_ID = None
APP_MASTER_KEY = None
ROUTER_URL = None
CLIENT_UA = None

def init_config():
    global APP_KEY
    global APP_ID
    global APP_MASTER_KEY
    global ROUTER_URL
    global CLIENT_UA

    cfg = ConfigParser()
    cfg.read('config.ini')

    APP_ID = cfg.get('prod', "appid")
    APP_KEY = cfg.get('prod', 'appkey')
    APP_MASTER_KEY = cfg.get('prod', 'app_master_key')
    CLIENT_UA = cfg.get('prod', 'ua')
    ROUTER_URL = "https://%s.%s" % (APP_ID[0:8], cfg.get('prod', 'im_router_addr_url_postfix'))
