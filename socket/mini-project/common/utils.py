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
