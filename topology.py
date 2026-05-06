"""
Network Topology Simulator - Simulates a 3-node network (Node A -> Router -> Node B).

OSI Layer Coverage:
  - Layer 3 (Network): IP addressing, packet routing, forwarding decisions
  - Layer 2 (DataLink): Frame-level packet encapsulation at each hop
  - Layer 1 (Physical): Simulated transmission delays between nodes
"""

import time
from datetime import datetime


class NetworkNode:
    """
    Represents a network node (host) with an IP address.

    OSI Layer: Layer 3 (Network) - each node has an IP address for
    network-layer identification and packet origination/destination.
    Layer 2 (DataLink) - packets are encapsulated into frames for transmission.
    """

    def __init__(self, name, ip_address):
        """
        Initialize a network node.

        OSI Layer: Layer 3 (Network) - assigns a unique IP address
        to identify the node on the network.
        """
        self.name = name
        self.ip_address = ip_address
        self.packets_sent = 0
        self.packets_received = 0

    def send(self, packet, next_hop):
        """
        Send a packet to the next hop in the network path.

        OSI Layer: Layer 3 (Network) - creates an IP packet with source
        and destination addresses, then passes it to the next hop (router or host).
        Layer 2 (DataLink) - the packet is wrapped in a frame for the physical link.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        print(f"\n{'=' * 60}")
        print(f"[{timestamp}] {self.name} -> Sending Packet")
        print(f"{'=' * 60}")
        print(f"  Source IP:      {self.ip_address}")
        print(f"  Destination IP: {packet['dest_ip']}")
        print(f"  Next Hop:       {next_hop.ip_address}")
        print(f"  TTL:            {packet['ttl']}")
        print(f"  Protocol:       {packet['protocol']}")
        print(f"  Payload:        {packet['payload']}")
        print(f"  [Layer 3 - Network]   IP packet constructed")
        print(f"  [Layer 2 - DataLink]  Frame encapsulated for transmission")
        print(f"  [Layer 1 - Physical]  Bits transmitted on wire")

        self.packets_sent += 1

        # Forward packet to next hop with simulated delay
        return next_hop.receive(packet, self)

    def receive(self, packet, from_node):
        """
        Receive a packet from another node.

        OSI Layer: Layer 3 (Network) - checks if the packet's destination
        IP matches this node's IP address (deliver or forward decision).
        Layer 2 (DataLink) - decapsulates the frame to extract the IP packet.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        print(f"\n{'=' * 60}")
        print(f"[{timestamp}] {self.name} <- Receiving Packet")
        print(f"{'=' * 60}")
        print(f"  From:           {from_node.ip_address}")
        print(f"  Source IP:      {packet['source_ip']}")
        print(f"  Destination IP: {packet['dest_ip']}")
        print(f"  TTL:            {packet['ttl']}")
        print(f"  [Layer 2 - DataLink]  Frame received and decapsulated")
        print(f"  [Layer 3 - Network]   IP packet extracted")

        self.packets_received += 1

        # Check if this node is the final destination
        if packet["dest_ip"] == self.ip_address:
            print(f"  [Layer 3 - Network]   Destination match! Delivering to application")
            print(f"  [Layer 7 - Application] Payload delivered: '{packet['payload']}'")
            return True
        else:
            print(f"  [Layer 3 - Network]   Not final destination. Forwarding required.")
            return False


class Router(NetworkNode):
    """
    Represents a network router that forwards packets between nodes.

    OSI Layer: Layer 3 (Network) - the router's primary function is to
    examine IP packet headers and make forwarding decisions based on the
    destination IP address and routing table.
    """

    def __init__(self, name, ip_address):
        """
        Initialize a router with a routing table.

        OSI Layer: Layer 3 (Network) - creates a routing table that maps
        destination networks to outgoing interfaces (next-hop addresses).
        """
        super().__init__(name, ip_address)
        # Routing table: maps destination network/prefix to (next_hop, interface)
        self.routing_table = {}

    def add_route(self, destination_network, next_hop_ip, interface):
        """
        Add an entry to the routing table.

        OSI Layer: Layer 3 (Network) - builds the routing table used for
        longest-prefix-match lookups when forwarding packets.
        """
        self.routing_table[destination_network] = {
            "next_hop": next_hop_ip,
            "interface": interface
        }
        print(f"  [Layer 3 - Network] Route added: {destination_network} via {next_hop_ip} ({interface})")

    def forward_packet(self, packet, from_node, connected_nodes):
        """
        Forward a packet based on routing table lookup.

        OSI Layer: Layer 3 (Network) - performs routing table lookup to
        determine the best next hop for the packet's destination IP.
        Decrements TTL (Time-To-Live) to prevent routing loops.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        dest_ip = packet["dest_ip"]

        print(f"\n{'=' * 60}")
        print(f"[{timestamp}] {self.name} - Routing Decision")
        print(f"{'=' * 60}")
        print(f"  Packet from:    {from_node.ip_address}")
        print(f"  Destination:    {dest_ip}")
        print(f"  [Layer 3 - Network]   Examining IP header")
        print(f"  [Layer 3 - Network]   Looking up routing table...")

        # Find the best route for the destination
        next_hop_node = None
        best_route = None

        for network, route in self.routing_table.items():
            # Simple prefix matching: check if dest IP starts with network prefix
            if dest_ip.startswith(network) or network == "0.0.0.0/0":
                best_route = route
                break

        if best_route:
            next_hop_ip = best_route["next_hop"]
            interface = best_route["interface"]

            # Find the connected node matching the next hop
            for node in connected_nodes:
                if node.ip_address == next_hop_ip:
                    next_hop_node = node
                    break

            print(f"  [Layer 3 - Network]   Match found: {dest_ip} -> {next_hop_ip} ({interface})")

            # Decrement TTL (Time-To-Live)
            packet["ttl"] -= 1
            print(f"  [Layer 3 - Network]   TTL decremented: {packet['ttl'] + 1} -> {packet['ttl']}")

            if packet["ttl"] <= 0:
                print(f"  [Layer 3 - Network]   TTL expired! Dropping packet.")
                return False

            if next_hop_node:
                # Simulate routing delay (processing + queuing delay)
                print(f"  [Layer 1 - Physical]  Forwarding with artificial delay...")
                time.sleep(0.05)  # 50ms simulated routing delay

                print(f"  [Layer 3 - Network]   Forwarding packet to {next_hop_node.name}")
                return next_hop_node.receive(packet, self)
            else:
                print(f"  [Layer 3 - Network]   Next hop {next_hop_ip} not reachable!")
                return False
        else:
            print(f"  [Layer 3 - Network]   No route found for {dest_ip}!")
            print(f"  [Layer 3 - Network]   Packet dropped - destination unreachable")
            return False


def simulate_network():
    """
    Simulate a complete 3-node network topology: Node A -> Router -> Node B.

    OSI Layer: Layer 3 (Network) - demonstrates end-to-end packet delivery
    across a routed network, showing how IP packets traverse from source
    to destination via an intermediate router.

    The simulation shows:
    1. Packet creation at Node A (source)
    2. Router receives packet, performs routing table lookup, and forwards
    3. Node B (destination) receives and processes the packet
    """
    print("\n" + "#" * 60)
    print("#" + " " * 58 + "#")
    print("#   TCP/IP Network Topology Simulator                          #")
    print("#   Topology: Node A --> Router --> Node B                     #")
    print("#" + " " * 58 + "#")
    print("#" * 60)

    # Create network nodes (Layer 3: Network layer addressing)
    print("\n--- Initializing Network Topology ---")
    node_a = NetworkNode("Node A", "192.168.1.10")
    router = Router("Router", "10.0.0.1")
    node_b = NetworkNode("Node B", "172.16.0.20")

    print(f"  Node A IP: {node_a.ip_address}")
    print(f"  Router IP: {router.ip_address}")
    print(f"  Node B IP: {node_b.ip_address}")

    # Configure routing table on the router (Layer 3: Network layer)
    print("\n--- Configuring Router ---")
    router.add_route("192.168.1.", "192.168.1.10", "eth0")  # Route to Node A
    router.add_route("172.16.0.", "172.16.0.20", "eth1")    # Route to Node B
    router.add_route("0.0.0.0/0", "10.0.0.254", "eth2")     # Default route

    # Define connected nodes for forwarding lookup
    connected_nodes = [node_a, node_b]

    # Simulate packet transfers
    print("\n" + "#" * 60)
    print("#   Simulating Packet Transfers                                #")
    print("#" * 60)

    packets = [
        {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20",
         "ttl": 64, "protocol": "TCP", "payload": "Hello from Node A!"},
        {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20",
         "ttl": 64, "protocol": "TCP", "payload": "Testing routed connection..."},
        {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20",
         "ttl": 64, "protocol": "UDP", "payload": "UDP datagram via router"},
    ]

    results = []

    for i, packet in enumerate(packets, 1):
        print(f"\n{'*' * 60}")
        print(f"* Packet #{i} of {len(packets)}")
        print(f"* Payload: '{packet['payload']}'")
        print(f"{'*' * 60}")

        # Node A sends packet to Router
        packet["next_hop"] = router.ip_address
        delivered = node_a.send(packet, router)

        # Router forwards packet (not final destination)
        if not delivered:
            # Router receives and forwards to Node B
            router_forwarded = router.forward_packet(packet, node_a, connected_nodes)
            delivered = router_forwarded

        results.append({
            "packet_num": i,
            "payload": packet["payload"],
            "delivered": delivered
        })

    # Print summary
    print("\n" + "#" * 60)
    print("#   Transmission Summary                                       #")
    print("#" * 60)

    for result in results:
        status = "DELIVERED" if result["delivered"] else "FAILED"
        print(f"  Packet #{result['packet_num']}: '{result['payload']}' -> {status}")

    print(f"\n  Node A: {node_a.packets_sent} sent, {node_a.packets_received} received")
    print(f"  Router: {router.packets_sent} sent, {router.packets_received} received")
    print(f"  Node B: {node_b.packets_sent} sent, {node_b.packets_received} received")

    print("\n" + "#" * 60)
    print("#   Simulation Complete                                        #")
    print("#" * 60)


if __name__ == "__main__":
    simulate_network()
