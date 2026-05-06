import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topology import NetworkNode, Router


class TestNetworkNode(unittest.TestCase):
    def test_node_creation(self):
        node = NetworkNode("TestNode", "192.168.1.1")
        self.assertEqual(node.name, "TestNode")
        self.assertEqual(node.ip_address, "192.168.1.1")
        self.assertEqual(node.packets_sent, 0)
        self.assertEqual(node.packets_received, 0)

    def test_send_increments_counter(self):
        sender = NetworkNode("A", "192.168.1.10")
        receiver = NetworkNode("B", "172.16.0.20")
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 64, "protocol": "TCP", "payload": "test"}

        delivered = sender.send(packet, receiver)
        self.assertTrue(delivered)
        self.assertEqual(sender.packets_sent, 1)
        self.assertEqual(receiver.packets_received, 1)

    def test_receive_matching_destination(self):
        node = NetworkNode("B", "172.16.0.20")
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 64, "protocol": "TCP", "payload": "hello"}
        sender = NetworkNode("A", "192.168.1.10")

        result = node.receive(packet, sender)
        self.assertTrue(result)
        self.assertEqual(node.packets_received, 1)

    def test_receive_non_matching_destination(self):
        node = NetworkNode("C", "10.0.0.5")
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 64, "protocol": "TCP", "payload": "hello"}
        sender = NetworkNode("A", "192.168.1.10")

        result = node.receive(packet, sender)
        self.assertFalse(result)
        self.assertEqual(node.packets_received, 1)


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.router = Router("R1", "10.0.0.1")
        self.node_a = NetworkNode("A", "192.168.1.10")
        self.node_b = NetworkNode("B", "172.16.0.20")
        self.connected = [self.node_a, self.node_b]

        self.router.add_route("192.168.1.", "192.168.1.10", "eth0")
        self.router.add_route("172.16.0.", "172.16.0.20", "eth1")
        self.router.add_route("0.0.0.0/0", "10.0.0.254", "eth2")

    def test_routing_table_populated(self):
        self.assertEqual(len(self.router.routing_table), 3)
        self.assertIn("192.168.1.", self.router.routing_table)

    def test_forward_to_known_destination(self):
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 64, "protocol": "TCP", "payload": "test"}
        result = self.router.forward_packet(packet, self.node_a, self.connected)
        self.assertTrue(result)
        self.assertEqual(self.node_b.packets_received, 1)

    def test_forward_decrements_ttl(self):
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 64, "protocol": "TCP", "payload": "test"}
        self.router.forward_packet(packet, self.node_a, self.connected)
        self.assertEqual(packet["ttl"], 63)

    def test_ttl_expiry(self):
        packet = {"source_ip": "192.168.1.10", "dest_ip": "172.16.0.20", "ttl": 1, "protocol": "TCP", "payload": "test"}
        result = self.router.forward_packet(packet, self.node_a, self.connected)
        self.assertFalse(result)
        self.assertEqual(packet["ttl"], 0)

    def test_no_route_found(self):
        packet = {"source_ip": "192.168.1.10", "dest_ip": "99.99.99.99", "ttl": 64, "protocol": "TCP", "payload": "test"}
        empty_router = Router("R2", "10.0.0.2")
        result = empty_router.forward_packet(packet, self.node_a, [])
        self.assertFalse(result)

    def test_forward_default_route(self):
        packet = {"source_ip": "192.168.1.10", "dest_ip": "8.8.8.8", "ttl": 64, "protocol": "UDP", "payload": "dns"}
        result = self.router.forward_packet(packet, self.node_a, self.connected)
        self.assertFalse(result)
        self.assertEqual(packet["ttl"], 63)


if __name__ == "__main__":
    unittest.main()
