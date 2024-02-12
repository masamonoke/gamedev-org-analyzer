import logging

logging.basicConfig(
    format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

config = {}

with open("../secret.properties") as f:
    lines = f.readlines()
    for line in lines:
        a = line.split("=")
        config[a[0]] = a[1][:-1]


def config_get_key(key: str):
    return config[key]

REDIS_CACHE_PORT = 12100
IGDB_CACHE_PORT = 12101
