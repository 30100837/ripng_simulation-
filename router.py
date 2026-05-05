import sys
import socket
import threading
import time

from config import ROUTERS, UPDATE_INTERVAL, INFINITY
from message import encode_update, decode_update

# ---- initialisation --------------------------------------------------------

def build_routing_table(name):
    """Seed the table: own networks at cost 1, everything else at INFINITY."""
    own = set(ROUTERS[name]["networks"])
    all_networks = {net for r in ROUTERS.values() for net in r["networks"]}
    return {net: (1 if net in own else INFINITY) for net in all_networks}

def get_port(name):
    return ROUTERS[name]["port"]

def get_neighbour_port(name):
    return get_port(name)

# ---- display ----------------------------------------------------------------

def print_table(name, table):
    print(f"\n[Router {name}] Routing Table:")
    for dest, cost in sorted(table.items()):
        status = str(cost) if cost < INFINITY else "unreachable"
        print(f"  {dest}  cost {status}")

# ---- sender thread ----------------------------------------------------------

def sender(name, table, learned_from, lock, sock):
    neighbours = ROUTERS[name]["neighbours"]
    while True:
        time.sleep(UPDATE_INTERVAL)
        for neighbour in neighbours:
            with lock:
                # Split horizon: don't advertise a route back to the neighbour it came from.
                filtered = {dest: cost for dest, cost in table.items()
                            if learned_from.get(dest) != neighbour}
            data = encode_update(name, filtered)
            sock.sendto(data, ("127.0.0.1", get_port(neighbour)))

# ---- receiver thread --------------------------------------------------------

def receiver(name, table, learned_from, lock, sock):
    while True:
        try:
            data, _ = sock.recvfrom(4096)
        except (ConnectionResetError, OSError):
            # Windows fires ICMP port-unreachable errors back on the UDP socket.
            continue
        msg = decode_update(data)
        sender_name = msg["router"]
        routes = msg["routes"]

        changed = False
        with lock:
            for dest, advertised_cost in routes.items():
                new_cost = min(advertised_cost + 1, INFINITY)
                if new_cost < table.get(dest, INFINITY):
                    table[dest] = new_cost
                    learned_from[dest] = sender_name
                    changed = True

        if changed:
            with lock:
                print_table(name, table)

# ---- main -------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ROUTERS:
        print(f"Usage: python router.py <{'|'.join(ROUTERS)}>")
        sys.exit(1)

    name = sys.argv[1]
    table = build_routing_table(name)
    learned_from = {}  # dest -> neighbour name we learned this route from
    lock = threading.Lock()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", get_port(name)))

    print_table(name, table)

    threading.Thread(target=sender,   args=(name, table, learned_from, lock, sock), daemon=True).start()
    threading.Thread(target=receiver, args=(name, table, learned_from, lock, sock), daemon=True).start()

    # Keep main thread alive.
    while True:
        time.sleep(1)
