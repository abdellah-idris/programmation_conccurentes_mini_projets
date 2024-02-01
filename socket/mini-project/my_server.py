import json
import socket
import sys
import threading
import time

from common import utils

LOCALHOSTT = "127.0.0.1"

# global variables shred between threads (servers)
channelsDAO = {}
userDAO = {}
threadsDAO = {}
serversDAO = {}
inter_server_port = 9999





class Server(threading.Thread):
    def __init__(self, port_number):
        threading.Thread.__init__(self)
        self.port_number = port_number

    def run(self):
        global channelsDAO
        global userDAO
        global threadsDAO
        global serversDAO
        global LOCALHOSTT

        print("Server started at: ", LOCALHOSTT, ":", self.port_number)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCALHOSTT, self.port_number))

        print(f"{self.port_number}: Waiting for client request...")

        while True:
            try:
                server.listen()  # Listen for incoming connections
                clientsock, adresse = server.accept()
                new_thread = ThreadUser(adresse, clientsock)
                new_thread.start()
                print(f"{self.port_number}: new user: {new_thread.user.name}")

            except KeyboardInterrupt:
                print("KeyboardInterrupt detected ...")
                to_client = '/Disconnected'

                try:
                    for user_name, user_thread in threadsDAO.items():
                        print("Sending {} to user: {}".format('/Disconnected', user_name))
                        user_thread.user.socket.send(bytes(to_client, 'UTF-8'))
                        user_thread.user.socket.shutdown(socket.SHUT_RDWR)
                        user_thread.user.socket.close()

                except OSError:
                    pass
                exit(0)

class InterServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.port_number = 9999

    global threadsDAO
    global LOCALHOSTT

    def set_port_number(self, port_arg):
        self.port_number = port_arg

    def get_port_number(self):
        return self.port_number

    def handle_inter_server_communication(self, client_socket):
        print("Handling inter server communication...")
        data = client_socket.recv(1024)
        message = json.loads(data.decode('UTF-8'))

        command = message.get("command")
        print(command)
        if command == "list":
            content = message.get("content")
            # Process the inter-server message as needed
            print(f"Received inter-server message: {content}")
            print(f"sender: {message.get('sender')}")
            print(f"channel_name: {message.get('channel_name')}")
            print(f"server_port: {message.get('server_port')}")
            print(f"threadsDAO: {threadsDAO.keys()}")
            # Send the message to all connected clients that are in different servers
            for user_name, user_thread in threadsDAO.items():
                if user_name != message.get("sender"):
                    user_thread.user.socket.send(bytes(content, 'UTF-8'))

        client_socket.close()
    def run(self):
        print(f"Starting inter server : {LOCALHOSTT} : {self.port_number}")

        inter_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        inter_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        inter_server_socket.bind((LOCALHOSTT, self.port_number))
        inter_server_socket.listen()

        print(f"{self.port_number}: Waiting for client request...")

        while True:
            print(f"{self.port_number}:  Listened to communication")
            client_socket, client_address = inter_server_socket.accept()
            inter_server_thread = threading.Thread(target=self.handle_inter_server_communication, args=(client_socket, ))
            inter_server_thread.start()


class User:
    # A class with basic user information
    def __init__(self, adresse, clientsocket, name):
        self.adresse = adresse
        self.socket = clientsocket
        self.port = clientsocket.getsockname()[1]
        self.name = name
        self.away = False
        self.automatic_resp = ''


class Channel:
    # Manages channel information and user lists within the channel.
    def __init__(self, channel_name, key=None, admin=None):
        self.channel_name = channel_name
        self.key = key
        self.user_list = []  # List of users in the channel (User)
        self.admin = admin

    def get_channel_name(self):
        return self.channel_name

    def get_key(self):
        return self.key

    def get_user_list(self):
        return self.user_list

    def get_admin(self):
        return self.admin

    def update_user_list(self, user):
        self.user_list.append(user)


class ThreadUser(threading.Thread):
    # Handles user threading for messages and server communication.


    def __init__(self, adresse, client_socket):
        threading.Thread.__init__(self)
        self.user = User(adresse, client_socket, "Anonymous")
        self.stop = threading.Event()
        self.away = False
        self.automatic_resp = ''
        print(f"New thread started for {adresse} at {client_socket} ")

    def send_inter_server_message(self, command, content, sender=None, channel_name=None, server_port = None):
        # send message to server port 9999 (inter-server communication)
        inter_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to the server
            inter_server_socket.connect(("127.0.0.1", inter_server_port))

            # Prepare the message
            message = json.dumps({"command": command, "content": content})

            # Send the message
            inter_server_socket.sendall(message.encode('UTF-8'))

        except socket.error as e:
            print(f"Failed to send inter-server message: {e}")
            # todo check if the server is up else change the inter-server port
            # delete died server from the list of servers
            # change the port

        finally:
            # Close the connection
            inter_server_socket.close()


    def stop_thread(self):
        self.stop.set()

    def set_username(self, u_name):
        self.user.name = u_name

    def list(self):
        print("Displaying the list of channels")
        channels_names = set(channelsDAO.keys())
        if len(channels_names) == 0:
            self.user.socket.send(bytes("No channel available", 'UTF-8'))
            self.send_inter_server_message("list","No channel available", self.user.name, None, self.user.port)
        else:
            self.user.socket.send(bytes("Available channels :", 'UTF-8'))
            self.user.socket.send(bytes(str(channels_names), 'UTF-8'))
            self.send_inter_server_message("list", channels_names, self.user.name, None, self.user.port)

    def join_channel(self, msg):
        split_msg = msg.split()
        channel_to_join = split_msg[1]

        key = None
        if len(split_msg) == 3:
            key = split_msg[2]

        print(f"Attempting to join a channel {channel_to_join} with key {key}")

        if channel_to_join not in channelsDAO.keys():
            print(f"Creating a new channel {channel_to_join} with key {key} ")
            new_channel = Channel(channel_to_join, key, self.user.name)
            new_channel.update_user_list(User(self.user.adresse, self.user.socket, self.user.name))
            channelsDAO[channel_to_join] = new_channel
            self.user.socket.send(bytes(f"Creating a new channel {channel_to_join} with key {key} ", 'UTF-8'))

        else:
            canal = channelsDAO[channel_to_join]
            if canal.get_key() == key:
                print(f"The user has joined the channel {channel_to_join}")
                canal.update_user_list(User(self.user.adresse, self.user.socket, self.user.name))
                channelsDAO[channel_to_join] = canal
                self.user.socket.send(bytes(f"The user has joined the channel {channel_to_join}", 'UTF-8'))

            else:
                print('Incorrect channel password')
                print(f"key: {key}")
                self.user.socket.send(bytes("Incorrect channel password", 'UTF-8'))

    def names(self, msg):
        print('Displaying users in channels')

        channel_name = msg[7::]
        if channel_name != '':
            if channel_name not in channelsDAO.keys():
                self.user.socket.send(bytes('Channel not found', 'UTF-8'))

            else:
                names_display = [p.name for p in channelsDAO[channel_name].user_list]
                names_display = list(set(names_display))
                names_display.sort()
                self.user.socket.send(bytes(str(names_display), 'UTF-8'))

        else:
            print(f"Displaying users")
            # Displaying users in all channels
            names_display = userDAO.keys()
            names_display = list(set(names_display))
            names_display.sort()
            self.user.socket.send(bytes(str(names_display), 'UTF-8'))

    def send_away(self, msg):
        userDAO[self.user.name].away = not userDAO[self.user.name].away
        userDAO[self.user.name].automatic_resp = 'Automatic response from ' + self.user.name + ' : ' + msg[6::]
        self.away = not self.away
        self.automatic_resp = 'Automatic response from ' + self.user.name + ' : ' + msg[6::]

    def invite(self, msg):
        p_invited = msg[8::]
        print(self.user.name + " invited " + p_invited)

        if p_invited in userDAO.keys():
            # Retrieving the socket of the invited user
            target_socket = userDAO[p_invited].socket
            print(f"target_socket: {target_socket}")

            # Retrieving channels where the user is admin and channels without admin
            own_channels = {channel_name: channel for channel_name, channel in channelsDAO.items()
                            if channel.admin == self.user.name or channel.admin is None}
            print(f"own_channels: {own_channels}")

            # Add user to the invited channels
            for channel_name, channel in own_channels.items():
                channel.update_user_list(User(self.user.adresse, target_socket, p_invited))
                channelsDAO[channel_name] = channel

            target_socket.send(
                bytes(f"You have been invited by {self.user.name} in the channels {str(set(own_channels.keys()))}", 'UTF-8'))
        else:
            print("The invited user does not exist ")
            self.user.socket.send(bytes("The invited user does not exist ", 'UTF-8'))

    def msg(self, msg):
        # Send a private message to a user
        split_msg = msg.split()
        target = split_msg[1]
        msg_to_send = msg[len(split_msg[0]) + len(split_msg[1]) + 2::]
        print(f"Message to send: {msg_to_send} to target: {target}")

        # If it's a channel
        if target[0] == '#':
            channel_name = target

            if channel_name in channelsDAO:
                channel = channelsDAO[channel_name]
                user_is_in_chat_channel = any(user.name == self.user.name for user in channel.user_list)

                if not user_is_in_chat_channel:
                    print("Unable to send the message to this channel as you don't belong to it")
                    self.user.socket.send(
                        bytes("Unable to send the message to this channel as you don't belong to it", 'UTF-8'))
                else:
                    print(f"Sending the message to the channel {channel_name}")
                    target_sockets = [cl.socket for cl in channel.user_list]
                    for sockett in target_sockets:
                        sockett.send(bytes("(" + channel_name + ") " + self.user.name + ": " + msg_to_send, 'UTF-8'))
            else:
                print("The specified channel does not exist")
                self.user.socket.send(bytes("The specified channel does not exist", 'UTF-8'))

        else:  # Otherwise, it's a nickname (private message)
            nickname = target
            target_user = userDAO.get(nickname, None)

            if target_user:
                if target_user.away:
                    print("The user is away")
                    self.user.socket.send(bytes("The user is away" + target_user.automatic_resp, 'UTF-8'))
                else:
                    target_user.socket.send(
                        bytes("Private message from " + self.user.name + ": " + msg_to_send, 'UTF-8'))
            else:
                self.user.socket.send(bytes("The user does not exist", 'UTF-8'))

    def run(self):
        global inter_server_port
        global LOCALHOSTT
        global channelsDAO
        global userDAO
        global threadsDAO
        global serversDAO

        print(f"Connection from:  {self.user.adresse} with username: {self.user.name}")
        msg = ""
        while True:
            try:
                data = self.user.socket.recv(1024)
                msg = data.decode()
            except (KeyboardInterrupt, OSError):
                print(f"Closing thread for user {self.user.name}")
                exit(0)

            if msg[0:8] == "nickname":
                user_name = msg[9::]

                if user_name not in userDAO.keys():
                    self.set_username(user_name)
                    print("Username is: ", user_name)
                    userDAO[user_name] = self.user
                    threadsDAO[user_name] = ThreadUser(self.user.adresse, self.user.socket)

                    print(f"verifying user thread {threadsDAO.keys()}")

                else:
                    print('Username already exists')
                    self.user.socket.send(bytes('Username already exists', 'UTF-8'))
                    # Disconnect user
                    self.user.socket.shutdown(socket.SHUT_RDWR)
                    self.user.socket.close()
                    break

            elif msg == '/list':
                self.list()

            elif msg[0:6] == '/names':
                self.names(msg)

            elif msg[0:5] == '/join':
                self.join_channel(msg)

            elif msg[0:7] == '/invite':
                self.invite(msg)

            elif msg[0:4] == '/msg':
                self.msg(msg)

            elif msg[0:5] == '/away':
                self.send_away(msg)

        try:
            print("(", user_name, ")", "Client at: ", self.user.adresse, " disconnected...")
        except UnboundLocalError:
            print("User disconnected.")





if __name__ == "__main__":
    # Start the inter-server communication thread
    # Check if port 9999 is available
    if utils.check_port(9999):
        inter_server = InterServer()
        inter_server.start()
        time.sleep(0.1)

    else:
        print("Inter server is already running.")

    # start server
    if len(sys.argv) >= 2:
        for port in sys.argv[1:]:
            try:
                if utils.check_port(int(port)):
                    server = Server(int(port))
                    server.start()
                    time.sleep(0.1)

                else:
                    print(f"Server already running on port: {port}")

            except ValueError:
                print("Invalid port number. Please provide a valid integer.")

