import json


def encode_update(router_name, routing_table):
    payload = {"router": router_name, "routes": routing_table}
    return json.dumps(payload).encode()


def decode_update(data):
    return json.loads(data.decode())
