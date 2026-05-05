# Topology: A (5001) --- B (5002) --- C (5003)
# A and C only reach each other through B.

UPDATE_INTERVAL = 5  # seconds between periodic updates
INFINITY = 16        # unreachable hop count

ROUTERS = {
    "A": {
        "port": 5001,
        "neighbours": ["B"],
        "networks": ["2001:db8:1::/48"],
    },
    "B": {
        "port": 5002,
        "neighbours": ["A", "C"],
        "networks": ["2001:db8:2::/48"],
    },
    "C": {
        "port": 5003,
        "neighbours": ["B"],
        "networks": ["2001:db8:3::/48"],
    },
}
