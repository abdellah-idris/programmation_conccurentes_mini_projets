import socket
import threading
import re
import tkinter as tk

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


commands = ["/help", "/list", "/names", "/invite", "/msg", "/away", "/join"]

class IrcThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.client = client
        self.server_off = False

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            while not self.stop_event.is_set():
                data = self.client.recv(1024)
                if not data:
                    self.server_off = True
                    break
                msg = data.decode()
                msg_list.insert(tk.END, ' ' + msg)
                if msg == '/Disconnect' or msg == '':
                    print("Server disconnected...")
                    self.server_off = True
                    break
                else:
                    print(msg)
        except socket.error as e:
            print(f"Error: {e}")
            self.server_off = True

        if self.server_off:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()

def help_menu():
    msg_list.insert(tk.END, " Available commands:")
    msg_list.insert(tk.END, "   /away [message]")
    msg_list.insert(tk.END, "   /help")
    msg_list.insert(tk.END, "   /invite <nick>")
    msg_list.insert(tk.END, "   /join <canal> [clé]")
    msg_list.insert(tk.END, "   /list")
    msg_list.insert(tk.END, "   /msg [canal|nick] message ")
    msg_list.insert(tk.END, "   /names [channel]")
    msg_list.insert(tk.END, " ________________________________")

def send(event=None):
    if not username_entry.get():
        msg_list.insert(tk.END, " Please set your username first.")
        return

    if stream_thread.server_off:
        msg_list.insert(tk.END, " Server is off... ")
        print(" Server is off... ")
        stream_thread.stop()
        client.close()

    try:
        to_server = entry_field.get()
        print(f"to_server: {to_server}")
        if bool(re.match('^ *$', to_server)):
            print("Please enter a command/message")
            msg_list.insert(tk.END, " Please enter a command/message")
        else:
            msg_list.insert(tk.END, to_server)
            print(to_server)

            if to_server.split()[0] in commands and re.match(commands_regex[to_server.split()[0]], to_server):
                if to_server.split()[0] == '/help':
                    help_menu()
                else:
                    client.sendall(bytes(to_server, 'UTF-8'))
            else:
                msg_list.insert(tk.END, ' Unavailable or incorrect command! ')
                print('Unavailable or incorrect command! ')

    except (KeyboardInterrupt, ValueError, BrokenPipeError):
        print("Server disconnected...")
        msg_list.insert(tk.END, " Server disconnected...")

        to_server = '/Disconnect'
        try:
            client.sendall(bytes(to_server, 'UTF-8'))
        except (KeyboardInterrupt, ValueError, BrokenPipeError):
            pass
        finally:
            stream_thread.stop()
            client.close()

    entry_field.delete(0, 'end')


def initialize_username():
    user = username_entry.get()
    if user:
        to_server = "nickname:" + user
        client.sendall(bytes(to_server, 'UTF-8'))
        msg_list.insert(tk.END, f"User: {user}")
        print(f"User: {to_server[9::]}")
        username_entry.config(state='disabled')
        initialize_username_button.config(state='disabled')

top = tk.Tk()
general_font = ('New roman', 10)
top.option_add('*Font', general_font)
top.title("Internet Relay Chat")

# Username Entry
username_frame = tk.Frame(top)
username_label = tk.Label(username_frame, text="Username:")
username_label.pack(side=tk.LEFT)
username_entry = tk.Entry(username_frame)
username_entry.pack(side=tk.LEFT)
username_frame.pack(pady=5)

# Messages Frame
messages_frame = tk.Frame(top)
bar_vertical = tk.Scrollbar(messages_frame, orient=tk.VERTICAL)
bar_vertical.pack(side=tk.RIGHT, fill=tk.Y)
bar_horizental = tk.Scrollbar(messages_frame, orient=tk.HORIZONTAL)
bar_horizental.pack(side=tk.BOTTOM, fill=tk.X)
msg_list = tk.Listbox(messages_frame, height=20, width=70, yscrollcommand=bar_vertical.set, xscrollcommand=bar_horizental.set)
bar_vertical.config(command=msg_list.yview)
bar_horizental.config(command=msg_list.xview)
msg_list.pack(side=tk.LEFT, fill=tk.BOTH)
msg_list.pack()
messages_frame.pack()

# Entry Field Frame
entry_field_frame = tk.Frame(top)
entry_field = tk.Entry(entry_field_frame, width=50)
entry_field.bind("<Return>", send)
entry_field.pack(side=tk.LEFT)
# send_button = tk.Button(entry_field_frame, text="Send", command=send)
# send_button.pack(side=tk.LEFT)
entry_field_frame.pack(pady=10)

# Initialize username
initialize_username_button = tk.Button(top, text="Set Username", command=initialize_username)
initialize_username_button.pack(pady=5)

def on_closing():
    stream_thread.stop()
    client.close()
    top.destroy()

top.protocol("WM_DELETE_WINDOW", on_closing)

my_msg = tk.StringVar()
stream_thread = IrcThread(client)
stream_thread.start()

tk.mainloop()
