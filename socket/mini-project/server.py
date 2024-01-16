import socket
import threading

class user():
    def __init__(self, adresse, clientsocket, name):
        self.adresse = adresse
        self.socket = clientsocket
        self.name = name
        self.away =  False
        self.automatic_resp = ''

class channel():
    def __init__(self, channel_name, key=None):
        self.channel_name = channel_name
        self.key = key
        self.userlist = []

    def update_userlist(self, user):
        self.userlist.append(user)
    
channels = ["#general", "#random"]
user_list = []
threads = []

class ThreadUser(threading.Thread):
    def __init__(self, adresse, clientsocket):
        threading.Thread.__init__(self)
        self.user = user(adresse, clientsocket, "Anonymous")
        self.stop = threading.Event()

        self.away =  False
        self.automatic_resp = ''
        print (f"New thread started for {adresse} at {clientsocket} ")
        
    def stop(self):
        self.stop.set()
    
    def set_username(self, u_name):
        self.user.name = u_name

    
    def list(self):
        print("affichage de la liste des channels")
        channels_names=[ l.channel_name for l in channels]
        channels_names.sort()
        self.user.socket.send(bytes(str(channels_names), 'UTF-8'))
        
 
    def join(self, msg):
        split_msg = msg.split()
        chan_tojoin = split_msg[1]
        
        if len(split_msg) == 3:
            key = split_msg[2]
        else:
            key=None
            
        print("Tentative de rejoindre un channel")
        channels_names= [l.channel_name for l in channels]
        i=-1 
        if chan_tojoin in channels_names:
            i = channels_names.index(chan_tojoin)

        if i == -1:
            print("Création d'un nouveau channel")
            new_channel=channel(chan_tojoin, key)
            new_channel.update_userlist(user(self.user.adresse, self.user.socket, self.user.name))
            channels.append(new_channel)
        else:
            if channels[i].key == key:
                print("Le user a rejoint le channel")
                channels[i].update_userlist(user(self.user.adresse, self.user.socket, self.user.name))
            else:
                print('Mot de passe du canal incorrect')
                self.user.socket.send(bytes("Mot de passe du canal incorrect", 'UTF-8'))
                
    
    def names(self, msg):
        print('Affichage des utilisateurs des canaux')
        channel_name = msg[7::]
        if channel_name != '':                    
            channels_names = [l.channel_name for l in channels]
            i =-1 
            if channel_name in channels_names:
                i = channels_names.index(channel_name)
            if i ==-1:
                self.user.socket.send(bytes('Canal non trouvé', 'UTF-8'))
            else: 
                names_display=[p.name for p in channels[i].userlist]
                names_display=list(set(names_display))    
                names_display.sort()
                self.user.socket.send(bytes(str(names_display), 'UTF-8'))

        else:
            names_display= [p.name for channel in channels for p in channel.userlist] 
            names_display= list(set(names_display))    
            names_display.sort()
            self.user.socket.send(bytes(str(names_display), 'UTF-8'))
            
    def send_away(self, msg):
        ind = [i for i in range(len(user_list)) if user_list[i].name == self.user.name]
        user_list[ind[0]].away = not user_list[ind[0]].away
        user_list[ind[0]].automatic_resp= 'Réponse automatique de '+user_list[ind[0]].name +' : '+ msg[6::]
        self.away = not self.away
        self.automatic_resp = 'Réponse automatique de '+ self.user.name +' : '+ msg[6::]
        

    def invite(self, msg):
        p_invited = msg[8::]
        print(self.user.name+" invited "+ p_invited)   
        own_channels=[ "( Channel: "+str(l.channel_name)+ ", Password: "+ str(l.key)+" )" for l in channels for cl in l.userlist  if cl.name == self.user.name]            
        target_socket=[cl.socket for cl in user_list if cl.name == p_invited]
        if target_socket != []:
            target_socket[0].send(bytes(self.user.name+" invited you to the channels below :"+str(own_channels), 'UTF-8'))            
        else:
            print("Le user invité n'existe pas ")
            self.user.socket.send(bytes("Le user invité n'existe pas ", 'UTF-8'))

        
    def msg(self, msg):
        split_msg = msg.split()
        target = split_msg[1]
        msg_to_send = msg[len(split_msg[0])+len(split_msg[1])+2::]
        
        # Si c'est un canal
        if target[0] == '#':
            channel_name = target

            channel_exists = [1 for i in range(len(channels))
                                     if channels[i].channel_name == channel_name]

            user_is_in_chatchannel = [1 for i in range(len(channels))
                                     for j in range(len(channels[i].userlist))
                                     if channels[i].channel_name == channel_name
                                      and channels[i].userlist[j].name == self.user.name ]

            if channel_exists == []:
                print("Le canal spécifié n'existe pas")
                self.user.socket.send(bytes("Le canal spécifié n'existe pas", 'UTF-8'))

            elif user_is_in_chatchannel == []:
                print("Impossible d'envoyer le message dans ce canal car vous n'y appartenez pas")
                self.user.socket.send(bytes("Impossible d'envoyer le message dans ce canal car vous n'y appartenez pas", 'UTF-8'))
            else:
            
                target_sockets= [cl.socket for i in range(len(channels)) 
                                                for cl in channels[i].userlist
                                                if channels[i].channel_name == channel_name]
                for socket in target_sockets:
                    socket.send(bytes("(" + channel_name + ") " + self.user.name + ": " + msg_to_send, 'UTF-8'))
                    

        else: # sinon nickname (donc message privé)
            nickname = target  
            target_user=[cl for cl in user_list if cl.name == nickname]
            
            if target_user != []:
                print(target_user[0].name)
                if target_user[0].away==True :

                    self.user.socket.send(bytes(target_user[0].automatic_resp, 'UTF-8'))   
                    
                else:

                    target_user[0].socket.send(bytes("Private message from " + self.user.name + "): " + 
                                                         msg_to_send, 'UTF-8'))

            else: # Utilisateur non trouvé
                self.user.socket.send(bytes("Le user n'existe pas", 'UTF-8')) 
    
          

    def run(self):        
        global user_list
        print ("Connection from : ", adresse)
        msg = ''
        while True:            
            try:
                data = self.user.socket.recv(1024)
                msg = data.decode()
            except (KeyboardInterrupt, OSError):
                print("Closing thread.")
                exit(0)
                break
                
            if msg[0:8] == "nickname":                
                user_name = msg[9::]
                names = [cl for cl in user_list if cl.name == user_name]
                print(names)
                if names == []:                    
                    self.set_username(user_name)
                    print("Username is: ", user_name)
                    user_list.append(user(self.user.adresse, self.user.socket, self.user.name))

                else:
                    print('Username deja existant')
                    self.user.socket.send(bytes('/Disconnect', 'UTF-8'))
          
                
            elif msg == '/list':             
                self.list()
                
            elif msg[0:6] == '/names':
                self.names(msg)

            elif msg[0:5] == '/join':
                self.join(msg)
                
            elif msg[0:7] == '/invite':
                self.invite(msg)
               
            elif msg[0:4] == '/msg':
                self.msg(msg)
                
            elif msg[0:5] == '/away':
                self.send_away(msg)
                              
        try:
            print ("(", user_name, ")", "Client à: ", adresse , " déconnecté...")
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
