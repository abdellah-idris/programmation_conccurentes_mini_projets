import socket
import threading

class User:
    def __init__(self, username, socket):
        self.username = username
        self.socket = socket

class Channel:
    def __init__(self, name):
        self.name = name
        self.users = []
        self.messages = []

def handle_client(client_socket, username):
    user = User(username, client_socket)
    user_list.append(user)

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message == '/disconnect':
                user_list.remove(user)
                break
            elif message.startswith('/join'):
                channel_name = message.split()[1]
                join_channel(user, channel_name)
            elif message.startswith('/msg'):
                send_private_message(user, message)
            elif message.startswith('/list'):
                list_channels(user)
            elif message.startswith('/names'):
                list_users(user, message)
            else:
                send_channel_message(user, message)
        except ConnectionResetError:
            user_list.remove(user)
            break

def join_channel(user, channel_name):
    channel = find_channel(channel_name)
    if channel:
        channel.users.append(user)
    else:
        new_channel = Channel(channel_name)
        new_channel.users.append(user)
        channel_list.append(new_channel)

def list_channels(user):
    channels = [channel.name for channel in channel_list]
    user.socket.send(bytes(str(channels), 'utf-8'))

def list_users(user, message):
    channel_name = message.split()[1] if len(message.split()) > 1 else None

    if channel_name:
        channel = find_channel(channel_name)
        if channel:
            users = [u.username for u in channel.users]
            user.socket.send(bytes(str(users), 'utf-8'))
        else:
            user.socket.send(bytes('Channel not found', 'utf-8'))
    else:
        all_users = [u.username for channel in channel_list for u in channel.users]
        user.socket.send(bytes(str(all_users), 'utf-8'))

def send_channel_message(user, message):
    channel_name, content = message.split(maxsplit=1)
    channel = find_channel(channel_name)
    if channel:
        formatted_message = f'({channel_name}) {user.username}: {content}'
        for u in channel.users:
            u.socket.send(bytes(formatted_message, 'utf-8'))

def send_private_message(sender, message):
    _, recipient, content = message.split(maxsplit=2)
    target_user = find_user(recipient)
    if target_user:
        formatted_message = f'(Private message from {sender.username}): {content}'
        target_user.socket.send(bytes(formatted_message, 'utf-8'))
    else:
        sender.socket.send(bytes('User not found', 'utf-8'))

def find_channel(channel_name):
    for channel in channel_list:
        if channel.name == channel_name:
            return channel
    return None

def find_user(username):
    for user in user_list:
        if user.username == username:
            return user
    return None

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 8080))
    server.listen(5)
    print("Server started. Waiting for connections...")

    while True:
        client_socket, client_address = server.accept()
        username = client_socket.recv(1024).decode('utf-8')
        print(f"New connection from {client_address}, username: {username}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket, username))
        client_thread.start()

if __name__ == "__main__":
    user_list = []
    channel_list = []
    start_server()
