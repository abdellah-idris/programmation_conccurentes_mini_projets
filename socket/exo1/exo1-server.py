import socket

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"  # localhost
    port = 12345  # Use the same port as in client.py

    server_socket.bind((host, port))
    server_socket.listen(1)

    print("Waiting for connection...")

    conn, addr = server_socket.accept()
    print(f"Connection from {addr}")

    while True:
        try:
            # Receive message from client
            received_message = conn.recv(1024)
            if not received_message:
                break
            print(f"Received message from client: {received_message.decode()}")

            # Send acknowledgment to client
            conn.send("Message received".encode())

            # Server sends a message to the client
            message_to_send = input("Enter a message to send to the client: ")
            conn.send(message_to_send.encode())
        except ConnectionResetError:
            print("Client disconnected.")
            break

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()

