import socket
import threading


class user():
    def __init__(self, adresse, clientsocket, name):
        self.adresse = adresse
        self.socket = clientsocket
        self.name = name
        self.away = False
        self.automatic_resp = ''


class channel():
    def __init__(self, channel_name, key=None, admin=None):
        self.channel_name = channel_name
        self.key = key
        self.userlist = []
        self.admin = admin

    def get_channel_name(self):
        return self.channel_name

    def get_key(self):
        return self.key

    def get_userlist(self):
        return self.userlist

    def get_admin(self):
        return self.admin


    def update_userlist(self, user):
        self.userlist.append(user)


channels = {"#general": channel("#general"), "#random": channel("#random")}
user_list = {}
threads = []


class ThreadUser(threading.Thread):
    def __init__(self, adresse, clientsocket):
        threading.Thread.__init__(self)
        self.user = user(adresse, clientsocket, "Anonymous")
        self.stop = threading.Event()
        self.away = False
        self.automatic_resp = ''
        print(f"New thread started for {adresse} at {clientsocket} ")

    def stop(self):
        self.stop.set()

    def set_username(self, u_name):
        self.user.name = u_name

    def list(self):
        print("affichage de la liste des channels")
        channels_names = set(channels.keys())
        self.user.socket.send(bytes("Available channels :", 'UTF-8'))
        self.user.socket.send(bytes(str(channels_names), 'UTF-8'))

    def join_channel(self, msg):
        split_msg = msg.split()
        channel_to_join = split_msg[1]

        key = None
        if len(split_msg) == 3:
            key = split_msg[2]

        print(f"Tentative de rejoindre un channel {channel_to_join} avec la clé {key}")

        if channel_to_join not in channels.keys():
            print(f"Création d'un nouveau channel {channel_to_join} avec la clé {key} ")
            new_channel = channel(channel_to_join, key, self.user.name)
            new_channel.update_userlist(user(self.user.adresse, self.user.socket, self.user.name))
            channels[channel_to_join] = new_channel
            self.user.socket.send(bytes(f"Création d'un nouveau channel {channel_to_join} avec la clé {key} ", 'UTF-8'))


        else:
            canal = channels[channel_to_join]
            if canal.get_key() == key:
                print(f"Le user a rejoint le channel {channel_to_join}")
                canal.update_userlist(user(self.user.adresse, self.user.socket, self.user.name))
                channels[channel_to_join] = canal
                self.user.socket.send(bytes(f"Le user a rejoint le channel {channel_to_join}", 'UTF-8'))

            else:
                print('Mot de passe du canal incorrect')
                print(f"key: {key}")
                self.user.socket.send(bytes("Mot de passe du canal incorrect", 'UTF-8'))

    def names(self, msg):
        print('Affichage des utilisateurs des canaux')

        channel_name = msg[7::]
        if channel_name != '':
            if channel_name not in channels.keys():
                self.user.socket.send(bytes('Canal non trouvé', 'UTF-8'))

            else:
                names_display = [p.name for p in channels[channel_name].userlist]
                names_display = list(set(names_display))
                names_display.sort()
                self.user.socket.send(bytes(str(names_display), 'UTF-8'))

        else:
            print(f"Affichage des utilisateurs")
            # Affichage des utilisateurs de tous les canaux
            names_display = user_list.keys()
            names_display = list(set(names_display))
            names_display.sort()
            self.user.socket.send(bytes(str(names_display), 'UTF-8'))

    def send_away(self, msg):
        ind = [i for i in range(len(user_list)) if user_list[i].name == self.user.name]
        user_list[ind[0]].away = not user_list[ind[0]].away
        user_list[ind[0]].automatic_resp = 'Réponse automatique de ' + user_list[ind[0]].name + ' : ' + msg[6::]
        self.away = not self.away
        self.automatic_resp = 'Réponse automatique de ' + self.user.name + ' : ' + msg[6::]

    def invite(self, msg):
        p_invited = msg[8::]
        print(self.user.name + " invited " + p_invited)

        # Récupération des canaux ou l'utilisateur est admin et des caneax sans admin
        own_channels = [channel_name for channel_name, channell in channels.items()
                        if channell.admin == self.user.name or channell.admin is None]
        print(f"own_channels: {own_channels}")

        # Récupération du socket de l'utilisateur invité
        target_socket = [userInfo.socket for user_name, userInfo in user_list.items() if user_name == p_invited]
        print(f"target_socket: {target_socket}")

        if target_socket:
            target_socket[0].send(
                bytes(self.user.name + " invited you to the channels below :" + str(own_channels), 'UTF-8'))
        else:
            print("Le user invité n'existe pas ")
            self.user.socket.send(bytes("Le user invité n'existe pas ", 'UTF-8'))

    def msg(self, msg):
        split_msg = msg.split()
        target = split_msg[1]
        msg_to_send = msg[len(split_msg[0]) + len(split_msg[1]) + 2::]
        print(f"Message to send: {msg_to_send} in target: {target}")
        # Si c'est un canal
        if target[0] == '#':
            channel_name = target

            channel_exists = [1 for i in range(len(channels))
                              if channels[i].channel_name == channel_name]

            user_is_in_chatchannel = [1 for i in range(len(channels))
                                      for j in range(len(channels[i].userlist))
                                      if channels[i].channel_name == channel_name
                                      and channels[i].userlist[j].name == self.user.name]

            if channel_exists == []:
                print("Le canal spécifié n'existe pas")
                self.user.socket.send(bytes("Le canal spécifié n'existe pas", 'UTF-8'))

            elif user_is_in_chatchannel == []:
                print("Impossible d'envoyer le message dans ce canal car vous n'y appartenez pas")
                self.user.socket.send(
                    bytes("Impossible d'envoyer le message dans ce canal car vous n'y appartenez pas", 'UTF-8'))
            else:

                target_sockets = [cl.socket for i in range(len(channels))
                                  for cl in channels[i].userlist
                                  if channels[i].channel_name == channel_name]
                for socket in target_sockets:
                    socket.send(bytes("(" + channel_name + ") " + self.user.name + ": " + msg_to_send, 'UTF-8'))


        else:  # sinon nickname (donc message privé)
            nickname = target
            target_user = [cl for cl in user_list if cl.name == nickname]

            if target_user != []:
                print(target_user[0].name)
                if target_user[0].away == True:

                    self.user.socket.send(bytes(target_user[0].automatic_resp, 'UTF-8'))

                else:

                    target_user[0].socket.send(bytes("Private message from " + self.user.name + "): " +
                                                     msg_to_send, 'UTF-8'))

            else:  # Utilisateur non trouvé
                self.user.socket.send(bytes("Le user n'existe pas", 'UTF-8'))

    def run(self):
        global user_list
        print("Connection from : ", adresse)
        msg = ''
        while True:
            try:
                data = self.user.socket.recv(1024)
                msg = data.decode()
            except (KeyboardInterrupt, OSError):
                print("Closing thread.")
                exit(0)

            if msg[0:8] == "nickname":
                user_name = msg[9::]

                if user_name not in user_list.keys():
                    self.set_username(user_name)
                    print("Username is: ", user_name)
                    user_list[user_name] = user(self.user.adresse, self.user.socket, self.user.name)

                else:
                    print('Username deja existant')
                    self.user.socket.send(bytes('Username deja existant', 'UTF-8'))
                    # disconnect user
                    self.user.socket.shutdown(socket.SHUT_RDWR)
                    self.user.socket.close()
                    break


            elif msg == '/list': #done
                self.list()

            elif msg[0:6] == '/names': #done
                self.names(msg)

            elif msg[0:5] == '/join': #done
                self.join_channel(msg)

            elif msg[0:7] == '/invite':
                self.invite(msg)

            elif msg[0:4] == '/msg':
                self.msg(msg)

            elif msg[0:5] == '/away':
                self.send_away(msg)

        try:
            print("(", user_name, ")", "Client à: ", adresse, " déconnecté...")
        except UnboundLocalError:
            print("User disconnected.")


LOCALHOST = "127.0.0.1"
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))

print("Serveur démarré.")
print("Waiting for client request...")

while True:
    try:
        server.listen(2)
        clientsock, adresse = server.accept()
        newthread = ThreadUser(adresse, clientsock)
        newthread.start()
        threads.append(newthread)

    except KeyboardInterrupt:
        print("KeyboardInterrupt détecté ...")
        to_client = '/Disconnect'
        try:

            for k in range(len(user_list)):
                print("Sending /Disconnect to user: ", user_list[k].name)
                user_list[k].socket.send(bytes(to_client, 'UTF-8'))
                user_list[k].socket.shutdown(socket.SHUT_RDWR)
                user_list[k].socket.close()

        except OSError:
            pass
        exit(0)
