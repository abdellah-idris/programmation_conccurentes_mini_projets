import socket


def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Timeout in case the port is not responding
    try:
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        sock.close()
        return True
    except socket.error:
        return False

def is_server_active(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)  # Timeout in seconds
            sock.connect(("127.0.0.1", port))
            return True  # Server is active and accepts connections
    except (ConnectionRefusedError, socket.timeout):
        return False  # Server is not active or does not accept connections

