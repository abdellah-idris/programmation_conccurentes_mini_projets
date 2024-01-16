import socket
import threading

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"{data.decode('utf-8')}")
        except ConnectionResetError:
            break

    client_socket.close()

def send_message(client_socket):
    while True:
        message = input("")
        client_socket.send(message.encode('utf-8'))

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("[*] Server listening on port 9999")

    while True:
        client, addr = server.accept()
        print(f"[*] Accepted connection from: {addr[0]}:{addr[1]}")

        client_handler = threading.Thread(target=handle_client, args=(client,))
        send_thread = threading.Thread(target=send_message, args=(client,))

        client_handler.start()
        send_thread.start()

if __name__ == "__main__":
    start_server()
