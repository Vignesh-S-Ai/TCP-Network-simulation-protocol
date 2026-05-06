"""
TCP Server - Simulates a TCP server with full handshake lifecycle logging.

OSI Layer Coverage:
  - Layer 4 (Transport): TCP socket creation, binding, listening, connection handling
  - Layer 5 (Session): Managing client sessions and connection state
  - Layer 7 (Application): Echoing received data back to clients
"""

import socket
import threading
import time
from datetime import datetime
import logging
import os

# Configure logging to write to server_log.txt with timestamps
LOG_FILE = "server_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler()
    ]
)

# Default configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000


def log_stage(stage, message, client_address=None):
    """
    Log a TCP protocol stage with timestamp.

    OSI Layer: Layer 4 (Transport) - logs TCP state transitions
    (SYN, SYN-ACK, ACK, DATA, FIN stages of the TCP connection lifecycle)
    """
    addr_str = f" from {client_address}" if client_address else ""
    log_entry = f"[{stage}] {message}{addr_str}"
    logging.info(log_entry)


def handle_client(client_socket, client_address):
    """
    Handle an individual client connection through its full lifecycle.

    OSI Layer: Layer 4 (Transport) - manages the TCP connection state
    for a single client from acceptance to teardown.
    Layer 7 (Application) - processes and echoes application data.
    """
    try:
        # [SYN-ACK] Server accepts the connection (responds to client SYN)
        log_stage("SYN-ACK", f"Connection accepted, sending SYN-ACK", client_address)

        # [ACK] Three-way handshake complete
        log_stage("ACK", f"Handshake complete, session established", client_address)

        # Data exchange loop - read messages from client
        message_count = 0
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message_count += 1
            decoded_data = data.decode("utf-8").strip()

            # [DATA] Log received message with timestamp
            log_stage("DATA", f"Message #{message_count}: '{decoded_data}'", client_address)

            # Echo response back to client (Application layer behavior)
            response = f"Server received: {decoded_data}"
            client_socket.sendall(response.encode("utf-8"))

        log_stage("DATA", f"Total messages received: {message_count}", client_address)

    except ConnectionResetError:
        log_stage("DATA", f"Connection reset by peer", client_address)
    except Exception as e:
        log_stage("DATA", f"Error handling client: {e}", client_address)
    finally:
        # [FIN] Connection teardown - four-way handshake begins
        log_stage("FIN", f"Closing connection, sending FIN", client_address)
        client_socket.close()
        log_stage("FIN", f"Connection closed successfully", client_address)


def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Start the TCP server and listen for incoming connections.

    OSI Layer: Layer 4 (Transport) - creates TCP socket, binds to address,
    and enters listening state (passive open).
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow socket reuse to avoid 'Address already in use' errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    log_stage("SYN", f"TCP Server started on {host}:{port}, waiting for connections...")

    try:
        while True:
            # Accept incoming connection (passive open completes)
            client_socket, client_address = server_socket.accept()

            # [SYN] Log incoming connection request
            log_stage("SYN", f"Connection received", client_address)

            # Spawn a new thread to handle this client
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        log_stage("FIN", "Server shutting down...")
    finally:
        server_socket.close()
        log_stage("FIN", "Server socket closed")


if __name__ == "__main__":
    print("=" * 60)
    print("TCP Network Simulator - Server")
    print("=" * 60)
    print(f"Starting server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    start_server()
