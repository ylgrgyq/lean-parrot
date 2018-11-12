import random
import string
import logging


def generate_id(size=10, chars=string.ascii_letters + string.digits):
    return ''.join(random.choices(chars, k=size))


def get_logger(logger_name):

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s %(message)s'))
    logger.addHandler(console)
    logging.getLogger('ws4py').addHandler(console)

    return logger


LOG = get_logger(__name__)


class Any:
    def __str__(self):
        return "ANY"

    def __repr__(self):
        return "ANY"


MATCH_ANY = Any()


def partial_match_json(expect, actual):
    if expect == MATCH_ANY:
        pass
    elif isinstance(expect, bool):
        if expect == False and actual is None:
            return True
        else:
            return actual == expect
    elif isinstance(expect, dict):
        if not isinstance(actual, dict):
            print('type failed %s not equals to %s' % (actual, expect))
            return False
        else:
            for k, expect_v in expect.items():
                actual_v = actual.get(k)
                if not partial_match_json(expect_v, actual_v):
                    return False
    elif isinstance(expect, (list, )):
        if not isinstance(actual, (list, )):
            print('type failed %s not equals to %s' % (actual, expect))
            return False
        for actual_v, expect_v in zip(actual, expect):
            if not partial_match_json(expect_v, actual_v):
                return False
    else:
        if actual != expect:
            return False
    return True
