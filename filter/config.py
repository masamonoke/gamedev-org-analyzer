config = {}

with open("../secret.properties") as f:
    lines = f.readlines()
    for line in lines:
        a = line.split("=")
        config[a[0]] = a[1][:-1]


def config_get_key(key: str):
    return config[key]
