import socket
import threading
import tkinter as tk
import re
from argparse import ArgumentParser, SUPPRESS

from irc.common import utils


class IrcClient:
    def __init__(self, server, port, username):
        self.server = server
        self.port = port
        self.username = username
        self.is_away = False  # Default status is not away

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

    def toggle_away_status(self):
        self.is_away = not self.is_away
        # Update the status indicator (circle)
        self.update_status_indicator()

    def update_status_indicator(self):
        # Clear any previous status indicator
        self.status_canvas.delete("all")

        # Determine the color based on away status
        color = "red" if self.is_away else "green"

        # Draw a circle as the status indicator
        x, y, radius = 10, 10, 5  # Adjust position and size as needed
        self.status_canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)

    def run(self):
        self.initialize_gui()
        self.stream_thread = IrcThread(self.client_socket, self.msg_list)
        self.stream_thread.start()
        self.initialize_username()
        self.gui.mainloop()

    def initialize_gui(self):
        self.gui = tk.Tk()
        self.gui.title("Multi Server IRC")

        # Set minimum size for the GUI
        self.gui.minsize(400, 400)  # Adjust the dimensions as needed

        # Create a frame for the status indicator
        status_frame = tk.Frame(self.gui)
        status_frame.pack(anchor=tk.W)  # Adjust anchor as needed

        # Create a canvas to draw the status indicator
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20)
        self.status_canvas.grid(row=0, column=0)  # Use grid layout

        # Create a label to display the username
        self.username_label = tk.Label(status_frame, text=f"User: {self.username}")
        self.username_label.grid(row=0, column=1, padx=5)  # Use grid layout

        # Update the status indicator based on the initial status
        self.update_status_indicator()

        # Messages Frame
        messages_frame = tk.Frame(self.gui)
        messages_frame.pack(fill=tk.BOTH, expand=True)

        bar_vertical = tk.Scrollbar(messages_frame, orient=tk.VERTICAL)
        bar_vertical.pack(side=tk.RIGHT, fill=tk.Y)

        bar_horizontal = tk.Scrollbar(messages_frame, orient=tk.HORIZONTAL)
        bar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

        self.msg_list = tk.Listbox(messages_frame, height=20, width=50,
                                   yscrollcommand=bar_vertical.set,
                                   xscrollcommand=bar_horizontal.set)
        bar_vertical.config(command=self.msg_list.yview)
        bar_horizontal.config(command=self.msg_list.xview)

        self.msg_list.pack(fill=tk.BOTH, expand=True)

        # Entry Field Frame
        entry_field_frame = tk.Frame(self.gui)
        entry_field_frame.pack(pady=10)
        self.entry_field = tk.Entry(entry_field_frame, width=40)
        self.entry_field.bind("<Return>", self.send)
        self.entry_field.grid(row=0, column=0, padx=5, pady=5)
        entry_field_frame.pack(pady=10)

        self.gui.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send(self, event=None):
        if self.stream_thread.server_off:
            self.msg_list.insert(tk.END, " Server is off :( Please Make sur to reconnect")
            print(" Server is off... Please Make sur to reconnect")
            self.stream_thread.stop()
            self.client_socket.close()
            return

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
                    elif to_server.split()[0] == '/away':
                        self.toggle_away_status()
                        self.client_socket.sendall(bytes(to_server, 'UTF-8'))

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
        to_server = "nickname:" + self.username
        self.client_socket.sendall(bytes(to_server, 'UTF-8'))
        # self.msg_list.insert(tk.END, f"User: {self.username}")
        print(f"User: {self.username}")
        self.entry_field.config(state='normal')

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
    parser.add_argument("username", type=str, help="Username")
    parser.add_argument("port", type=int, help="Port to connect to")
    args = parser.parse_args()

    LOCALHOST = "127.0.0.1"
    if utils.is_server_active(args.port):
        client_app = IrcClient(LOCALHOST, args.port, args.username)
        client_app.run()
    else:
        raise UserWarning(f"Server {LOCALHOST}:{args.port}  Not Running")