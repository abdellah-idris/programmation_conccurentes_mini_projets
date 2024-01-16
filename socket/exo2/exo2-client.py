import socket
import threading

def send_message(client_socket):
    while True:
        message = input("")
        client_socket.send(message.encode('utf-8'))

def receive_messages(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"{data.decode('utf-8')}")

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 9999))

    send_thread = threading.Thread(target=send_message, args=(client,))
    receive_thread = threading.Thread(target=receive_messages, args=(client,))

    send_thread.start()
    receive_thread.start()

if __name__ == "__main__":
    start_client()
