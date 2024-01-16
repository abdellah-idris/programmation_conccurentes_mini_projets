import socket

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"  # localhost
    port = 12345  # Use the same port as in server.py

    client_socket.connect((host, port))

    while True:
        try:
            # Client sends a message to the server
            message_to_send = input("Enter a message to send to the server: ")
            client_socket.send(message_to_send.encode())

            # Receive acknowledgment from the server
            acknowledgment = client_socket.recv(1024)
            print(f"Server acknowledgment: {acknowledgment.decode()}")

            # Receive message from the server
            received_message = client_socket.recv(1024)
            print(f"Received message from server: {received_message.decode()}")
        except ConnectionResetError:
            print("Server disconnected.")
            break

    client_socket.close()

if __name__ == "__main__":
    start_client()
