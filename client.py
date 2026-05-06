"""
TCP Client - Simulates a TCP client with full lifecycle and OSI layer labels.

OSI Layer Coverage:
  - Layer 4 (Transport): TCP socket creation, three-way handshake, data transfer
  - Layer 3 (Network): IP addressing and routing to destination
  - Layer 2 (DataLink): Frame-level acknowledgment labels
  - Layer 7 (Application): Sending and receiving application messages
"""

import socket
import time
from datetime import datetime
import logging

# Configure logging to write to client_log.txt with timestamps
LOG_FILE = "client_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler()
    ]
)

# Default server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000

# Sample messages to send during the session
SAMPLE_MESSAGES = [
    "Hello, this is message 1 from the TCP client",
    "Network simulation in progress - message 2",
    "Testing three-way handshake - message 3",
    "Data transfer verification - message 4",
    "Final message before teardown - message 5"
]


def log_layer(layer_name, layer_number, message):
    """
    Log a message with OSI layer label for clear protocol visualization.

    OSI Layer: Cross-layer utility - applies layer labels to all logged events
    so the terminal output clearly shows which OSI layer each operation belongs to.
    """
    log_entry = f"[Layer {layer_number} - {layer_name}] {message}"
    logging.info(log_entry)
    return datetime.now()


def tcp_handshake(client_socket, server_host, server_port):
    """
    Simulate and log the TCP three-way handshake.

    OSI Layer: Layer 4 (Transport) - the three-way handshake (SYN, SYN-ACK, ACK)
    is a Transport layer mechanism that establishes a reliable connection.
    Layer 3 (Network) - the connect() call uses the IP address to route packets.
    """
    log_layer("Transport", 4, f"Initiating TCP connection to {server_host}:{server_port}")
    log_layer("Network", 3, f"Resolving destination IP: {server_host}")
    log_layer("DataLink", 2, "Preparing Ethernet frame for local network")

    # Step 1: Client sends SYN (active open)
    log_layer("Transport", 4, "Sending [SYN] - Sequence number: 0")

    # connect() performs the TCP three-way handshake under the hood
    client_socket.connect((server_host, server_port))

    # Step 2: Server responds with SYN-ACK (simulated log - connect() already received it)
    log_layer("Transport", 4, "Received [SYN-ACK] - Acknowledgment number: 1")

    # Step 3: Client sends ACK (connect() already sent this)
    log_layer("Transport", 4, "Sending [ACK] - Sequence number: 1, Acknowledgment number: 1")
    log_layer("Transport", 4, "TCP Three-Way Handshake COMPLETE - Connection established")
    log_layer("Network", 3, f"Route confirmed: {server_host}:{server_port}")


def send_messages(client_socket, messages):
    """
    Send a list of messages to the server and receive responses.

    OSI Layer: Layer 4 (Transport) - reliable data transfer via TCP send/recv.
    Layer 7 (Application) - the actual message content is application data.
    """
    results = []

    for i, message in enumerate(messages, 1):
        # Application layer: prepare the message
        log_layer("Application", 7, f"Preparing message #{i}: '{message}'")

        # Transport layer: send data over TCP
        send_time = datetime.now()
        log_layer("Transport", 4, f"Sending message #{i} ({len(message)} bytes)")

        client_socket.sendall(message.encode("utf-8"))

        # Transport layer: receive response from server
        response = client_socket.recv(1024).decode("utf-8")
        recv_time = datetime.now()

        # Calculate latency
        latency = (recv_time - send_time).total_seconds() * 1000  # Convert to ms

        log_layer("Application", 7, f"Received response #{i}: '{response}'")
        log_layer("Transport", 4, f"Message #{i} latency: {latency:.2f} ms")

        results.append({
            "message_num": i,
            "message": message,
            "response": response,
            "latency_ms": latency,
            "send_time": send_time.isoformat(),
            "recv_time": recv_time.isoformat()
        })

        # Small delay between messages to simulate realistic traffic
        if i < len(messages):
            time.sleep(0.5)

    return results


def tcp_teardown(client_socket):
    """
    Simulate and log the TCP connection teardown (four-way handshake).

    OSI Layer: Layer 4 (Transport) - graceful connection termination
    using FIN/ACK exchange to close the TCP session.
    """
    log_layer("Transport", 4, "Initiating connection teardown")
    log_layer("Transport", 4, "Sending [FIN] - No more data to send")
    log_layer("Transport", 4, "Waiting for server [FIN]")

    # Close the socket - this sends FIN to the server
    client_socket.close()

    log_layer("Transport", 4, "Received [FIN] from server, sending [ACK]")
    log_layer("Transport", 4, "TCP Connection teardown COMPLETE")
    log_layer("Network", 3, "Route entry removed from connection table")
    log_layer("DataLink", 2, "Ethernet frame session terminated")


def run_client(server_host=DEFAULT_HOST, server_port=DEFAULT_PORT):
    """
    Run the full TCP client lifecycle: handshake -> data -> teardown.

    OSI Layer: All layers - orchestrates the complete communication
    from network addressing through application data exchange.
    """
    print("=" * 60)
    print("TCP Network Simulator - Client")
    print("=" * 60)
    print(f"Connecting to {server_host}:{server_port}")
    print("=" * 60)

    # Create TCP socket (Transport layer)
    log_layer("Transport", 4, "Creating TCP socket (AF_INET, SOCK_STREAM)")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Phase 1: Three-Way Handshake
        print("\n--- Phase 1: TCP Handshake ---")
        tcp_handshake(client_socket, server_host, server_port)

        # Phase 2: Data Transfer
        print("\n--- Phase 2: Data Transfer ---")
        results = send_messages(client_socket, SAMPLE_MESSAGES)

        # Phase 3: Connection Teardown
        print("\n--- Phase 3: Connection Teardown ---")
        tcp_teardown(client_socket)

        # Print summary
        print("\n" + "=" * 60)
        print("Client Session Summary")
        print("=" * 60)
        print(f"Messages sent: {len(results)}")
        print(f"Messages received: {len(results)}")
        avg_latency = sum(r["latency_ms"] for r in results) / len(results)
        print(f"Average latency: {avg_latency:.2f} ms")
        print(f"Total data sent: {sum(len(r['message']) for r in results)} bytes")
        print(f"Total data received: {sum(len(r['response']) for r in results)} bytes")
        print("=" * 60)

    except ConnectionRefusedError:
        log_layer("Transport", 4, f"Connection refused: Is the server running on {server_host}:{server_port}?")
    except Exception as e:
        log_layer("Transport", 4, f"Error: {e}")
    finally:
        print(f"\nLogs saved to {LOG_FILE}")


if __name__ == "__main__":
    run_client()
