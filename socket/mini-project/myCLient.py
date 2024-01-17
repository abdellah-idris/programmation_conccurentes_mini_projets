import socket
import threading
import tkinter as tk
import re
from argparse import ArgumentParser, SUPPRESS


class IrcClient:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.commands_regex = {
            "/help": "^/help$",
            "/list": "^/list$",
            "/names": "^/names$|^/names #[a-zA-Z0-9_]+$",
            "/invite": "^/invite [a-zA-Z0-9_]+$",
            "/msg": "^/msg #*[a-zA-Z0-9_]+ .+",  # allow characters like ?,§,!, etc
            "/away": "^/away$|^/away [a-zA-Z0-9_]+",
            "/join": "^/join #[a-zA-Z0-9_]+$|^/join #[a-zA-Z0-9_]+ [a-zA-Z0-9_]+$"
        }
        self.commands = ["/help", "/list", "/names", "/invite", "/msg", "/away", "/join"]
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server, self.port))
        self.client_socket.setblocking(True)
        self.stream_thread = None

    def run(self):
        self.initialize_gui()
        self.stream_thread = IrcThread(self.client_socket, self.msg_list)
        self.stream_thread.start()
        self.gui.mainloop()

    def initialize_gui(self):
        self.gui = tk.Tk()
        self.gui.title("Internet Relay Chat")

        # Username Entry
        username_frame = tk.Frame(self.gui)
        username_label = tk.Label(username_frame, text="Username:")
        username_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = tk.Entry(username_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        username_frame.pack(pady=5)

        # Messages Frame
        messages_frame = tk.Frame(self.gui)
        bar_vertical = tk.Scrollbar(messages_frame, orient=tk.VERTICAL)
        bar_vertical.pack(side=tk.RIGHT, fill=tk.Y)
        bar_horizontal = tk.Scrollbar(messages_frame, orient=tk.HORIZONTAL)
        bar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)
        self.msg_list = tk.Listbox(messages_frame, height=20, width=50, yscrollcommand=bar_vertical.set, xscrollcommand=bar_horizontal.set)
        bar_vertical.config(command=self.msg_list.yview)
        bar_horizontal.config(command=self.msg_list.xview)
        self.msg_list.pack(side=tk.LEFT, fill=tk.BOTH)
        self.msg_list.pack()
        messages_frame.pack()

        # Entry Field Frame
        entry_field_frame = tk.Frame(self.gui)
        self.entry_field = tk.Entry(entry_field_frame, width=40)
        self.entry_field.bind("<Return>", self.send)
        self.entry_field.grid(row=0, column=0, padx=5, pady=5)
        entry_field_frame.pack(pady=10)

        # Initialize username
        initialize_username_button = tk.Button(self.gui, text="Set Username", command=self.initialize_username)
        initialize_username_button.pack(pady=5)

        self.gui.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send(self, event=None):
        if not self.username_entry.get():
            self.msg_list.insert(tk.END, " Please set your username first.")
            return

        if self.stream_thread.server_off:
            self.msg_list.insert(tk.END, " Server is off... ")
            print(" Server is off... ")
            self.stream_thread.stop()
            self.client_socket.close()

        try:
            to_server = self.entry_field.get()
            print(f"to_server: {to_server}")
            if bool(re.match('^ *$', to_server)):
                print("Please enter a command/message")
                self.msg_list.insert(tk.END, " Please enter a command/message")
            else:
                self.msg_list.insert(tk.END, to_server)
                print(to_server)

                if self.is_valid_command(to_server):
                    if to_server.split()[0] == '/help':
                        self.help_menu()
                    else:
                        self.client_socket.sendall(bytes(to_server, 'UTF-8'))
                else:
                    self.msg_list.insert(tk.END, ' Unavailable or incorrect command! ')
                    print('Unavailable or incorrect command! ')

        except (KeyboardInterrupt, ValueError, BrokenPipeError):
            print("Server disconnected...")
            self.msg_list.insert(tk.END, " Server disconnected...")

            to_server = '/Disconnect'
            try:
                self.client_socket.sendall(bytes(to_server, 'UTF-8'))
            except (KeyboardInterrupt, ValueError, BrokenPipeError):
                pass
            finally:
                self.stream_thread.stop()
                self.client_socket.close()

        self.entry_field.delete(0, 'end')

    def is_valid_command(self, command):
        for pattern in self.commands_regex.values():
            if re.match(pattern, command):
                return True
        return False

    def help_menu(self):
        self.msg_list.insert(tk.END, " Available commands:")
        self.msg_list.insert(tk.END, "   /away [message]")
        self.msg_list.insert(tk.END, "   /help")
        self.msg_list.insert(tk.END, "   /invite <nick>")
        self.msg_list.insert(tk.END, "   /join <canal> [clé]")
        self.msg_list.insert(tk.END, "   /list")
        self.msg_list.insert(tk.END, "   /msg [canal|nick] message ")
        self.msg_list.insert(tk.END, "   /names [channel]")
        self.msg_list.insert(tk.END, " ________________________________")

    def initialize_username(self):
        user = self.username_entry.get()
        if user:
            to_server = "nickname:" + user
            self.client_socket.sendall(bytes(to_server, 'UTF-8'))
            self.msg_list.insert(tk.END, f"User: {user}")
            print(f"User: {to_server[9::]}")
            self.username_entry.config(state='disabled')

    def on_closing(self):
        self.stream_thread.stop()
        self.client_socket.close()
        self.gui.destroy()


class IrcThread(threading.Thread):
    def __init__(self, client_socket, msg_list):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.client_socket = client_socket
        self.server_off = False
        self.msg_list = msg_list

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            while not self.stop_event.is_set():
                data = self.client_socket.recv(1024)
                if not data:
                    self.server_off = True
                    break
                msg = data.decode()
                self.msg_list.insert(tk.END, ' ' + msg)
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
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()


if __name__ == "__main__":
    # Argument Parser
    parser = ArgumentParser(description="Internet Relay Chat Client", usage=SUPPRESS)
    parser.add_argument("port", nargs="?", type=int, default=8080, help="Port to connect to (default is 8080)")
    args = parser.parse_args()

    LOCALHOST = "127.0.0.1"
    client_app = IrcClient(LOCALHOST, args.port)
    client_app.run()
