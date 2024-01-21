import socket, threading
import re, sys
from tkinter import *
import tkinter
from threading import Thread
import time

SERVER = "127.0.0.1"
PORT = 8080
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))
client.setblocking(True)

commands_regex = { "/help"  : "^/help$",
                   "/list"  : "^/list$",
                   "/names" : "^/names$|^/names #[a-zA-Z0-9_]+$",
                   "/invite": "^/invite [a-zA-Z0-9_]+$",
                   "/msg"   : "^/msg #*[a-zA-Z0-9_]+ [a-zA-Z0-9_]+",
                   "/away"  : "^/away$|^/away [a-zA-Z0-9_]+",
                   "/join"  : "^/join #[a-zA-Z0-9_]+$|^/join #[a-zA-Z0-9_]+ [a-zA-Z0-9_]+$"
                }

commands = ["/help","/list","/names" ,"/invite","/msg" , "/away","/join"]

class IrcThread(threading.Thread): 
    def __init__(self, client):
        threading.Thread.__init__(self) 
        self.stop = threading.Event() 
        self.client = client
        self.server_off = 0

    def stop(self): 
        self.stop.set()
        
        
    def run(self):
        msg = ''
        while True: 

            try: 
                data = self.client.recv(1024)
                msg = data.decode()
                msg_list.insert(tkinter.END, ' '+msg)
                if msg == '/Disconnect' or msg == '':
                    print("Déconnexion du serveur ... ")
                    self.server_off = 1
                    self.client.shutdown(socket.SHUT_RDWR)
                    self.client.close()
                    self.stop()
                    exit(0)
                  
                else:                    
                    print (msg)
            except socket.error as e:                
                self.server_off = 1
                exit(0)
def help_menu():
    msg_list.insert(tkinter.END, " Voici les commandes disponibles: ")
    msg_list.insert(tkinter.END, "   /away [message]")
    msg_list.insert(tkinter.END, "   /help")
    msg_list.insert(tkinter.END, "   /invite <nick>")
    msg_list.insert(tkinter.END, "   /join <canal> [clé]")
    msg_list.insert(tkinter.END, "   /list")
    msg_list.insert(tkinter.END, "   /msg [canal|nick] message ")
    msg_list.insert(tkinter.END, "   /names [channel]")
    msg_list.insert(tkinter.END, " __________________________________")
        
def send(event=None):
    
    if stream_thread.server_off == 1:
        msg_list.insert(tkinter.END, " Server is off... ")
        print(" Server is off... ")
        stream_thread.stop()
        client.close()
    try:
        to_server = my_msg.get()
        
        if bool(re.match('^ *$', to_server)):
            
            print("Veuillez saisir une commande/message")
            msg_list.insert(tkinter.END, " Veuillez saisir une commande/message")
        else:
            msg_list.insert(tkinter.END, to_server)
            print(to_server)

            if to_server.split()[0] in commands and bool(re.match(commands_regex[to_server.split()[0]], to_server)):
                if to_server.split()[0] == '/help':
                    help_menu()
                else:
                    client.sendall(bytes(to_server,'UTF-8'))   
            else:
                msg_list.insert(tkinter.END, ' Commande indisponible ou incorrecte ! ')
                print('Commande indisponible ou incorrecte ! ')


    except (KeyboardInterrupt, ValueError, BrokenPipeError):
        print("Déconnexion du serveur ...")
        msg_list.insert(tkinter.END, " Déconnexion du serveur  ...")

        to_server = '/Disconnect'
        try:            
            client.sendall(bytes(to_server,'UTF-8'))
        except (KeyboardInterrupt, ValueError, BrokenPipeError):
            pass

        finally:
            stream_thread.stop()
            client.close()
            
    entry_field.delete(0, 'end')
                
                
top = tkinter.Tk()

general_font = ('New roman', 14, 'bold')
top.option_add('*Font', general_font)
top.title("Internet Relay Chat")

# Affichage des messages
my_msg = tkinter.StringVar()
messages_frame = tkinter.Frame(top)

bar_vertical = tkinter.Scrollbar(messages_frame, orient = VERTICAL)
bar_vertical.pack(side= RIGHT,fill=Y)

bar_horizental = tkinter.Scrollbar(messages_frame, orient = HORIZONTAL)
bar_horizental.pack(side= BOTTOM ,fill=X)

msg_list = tkinter.Listbox(messages_frame, height = 30, width = 70, yscrollcommand=bar_vertical.set, xscrollcommand=bar_horizental.set )
bar_vertical.config(command = msg_list.yview)
bar_horizental.config(command=msg_list.xview)

msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

# Champs de saisie des commandes/messages
entry_field = tkinter.Entry(top, textvariable= my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()

send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()


username = str(sys.argv[1])
to_server = "nickname:" + username
client.sendall(bytes(to_server, 'UTF-8'))

msg_list.insert(tkinter.END, " L'utilisateur: "+ str(username))
print("L'utilisateur: ", to_server[9::])


help_menu()


time.sleep(1) 

stream_thread = IrcThread(client)
stream_thread.start()

tkinter.mainloop()
