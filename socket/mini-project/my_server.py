import socket
import sys
import threading


class User:
    def __init__(self, adresse, clientsocket, name):
        self.adresse = adresse
        self.socket = clientsocket
        self.name = name
        self.away = False
        self.automatic_resp = ''


class Channel:
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


channelsDAO = {}
userDAO = {}
threadsDAO = {}


class ThreadUser(threading.Thread):
    def __init__(self, adresse, client_socket):
        threading.Thread.__init__(self)
        self.user = User(adresse, client_socket, "Anonymous")
        self.stop = threading.Event()
        self.away = False
        self.automatic_resp = ''
        print(f"New thread started for {adresse} at {client_socket} ")

    def stop_thread(self):
        self.stop.set()

    def set_username(self, u_name):
        self.user.name = u_name

    def list(self):
        print("Displaying the list of channels")
        channels_names = set(channelsDAO.keys())
        self.user.socket.send(bytes("Available channels :", 'UTF-8'))
        self.user.socket.send(bytes(str(channels_names), 'UTF-8'))

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
        global userDAO
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


def start_server(port=8080):
    LOCALHOST = "127.0.0.1"

    print("Server started at: ", LOCALHOST, ":", port)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, port))

    print("Waiting for client request...")

    while True:
        try:
            server.listen(2)
            clientsock, adresse = server.accept()
            new_thread = ThreadUser(adresse, clientsock)
            new_thread.start()
            threadsDAO[new_thread.user.name] = new_thread

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


if __name__ == "__main__":
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
            start_server(port)
        except ValueError:
            print("Invalid port number. Please provide a valid integer.")
    else:
        print("Usage: python my_server.py <port>")
        print("Using default port 8080")
        start_server()
