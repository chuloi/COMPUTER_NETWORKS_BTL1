import socket
import threading
import os
import tkinter as tk
from tkinter import messagebox, filedialog

class FileSharingClient:
    def __init__(self, server_ip, server_port, peer_port=10000):
        self.server_ip = server_ip
        self.server_port = server_port
        self.peer_port = peer_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

        self.root = tk.Tk()
        self.root.title("File Sharing Client")

        # Set window height and width
        self.root.geometry("450x300")

        # File Entry Section
        file_entry_frame = tk.Frame(self.root)
        file_entry_frame.grid(row=0, column=0, columnspan=3, pady=(10, 0))

        self.file_label = tk.Label(file_entry_frame, text="Select File:")
        self.file_label.grid(row=0, column=0, padx=(0, 5))

        self.file_entry = tk.Entry(file_entry_frame, width=50)
        self.file_entry.grid(row=0, column=1)

        self.browse_button = tk.Button(file_entry_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=(5, 0))

        # Button Section
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 10))

        self.publish_button = tk.Button(button_frame, text="Publish", command=self.publish_file, width=10)
        self.publish_button.grid(row=0, column=0, padx=(0, 5))

        self.fetch_button = tk.Button(button_frame, text="Fetch", command=self.fetch_file, width=10)
        self.fetch_button.grid(row=0, column=1, padx=(5, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.disconnect)
        threading.Thread(target=self.start_peer_server, daemon=True).start()
        self.root.mainloop()

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

    def connect_to_server(self):
        try:
            self.socket.connect((self.server_ip, self.server_port))
            print("Connected to server.")
        except socket.error as e:
            print(f"Error connecting to server: {e}")

    def publish_file(self):
        file_path = self.file_entry.get()
        if not file_path:
            messagebox.showwarning("Error", "Please select a file.")
            return
        if not os.path.isfile(file_path):
            messagebox.showwarning("Error", "File not found.")
            return

        file_name = os.path.basename(file_path)
        message = f"publish {file_name}"
        self.socket.send(message.encode('utf-8'))
        response = self.socket.recv(1024).decode('utf-8')
        messagebox.showinfo("Publish", response)

    def fetch_file(self):
        file_name = self.file_entry.get()
        if not file_name:
            messagebox.showwarning("Error", "Please enter a file name.")
            return

        message = f"fetch {file_name}"
        self.socket.send(message.encode('utf-8'))
        sources = self.socket.recv(1024).decode('utf-8').split()
        if sources:
            self.fetch_file_from_peer(sources[0], file_name)
        else:
            messagebox.showinfo("Fetch", "File not found on the network.")

    def fetch_file_from_peer(self, peer_ip, file_name):
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, self.peer_port))
            messagebox.showinfo("Fetch", f"Connecting to peer at {peer_ip} to download {file_name}")
            peer_socket.send(f"GET {file_name}".encode('utf-8'))
            with open(file_name, 'wb') as file:
                while True:
                    file_data = peer_socket.recv(1024)
                    if not file_data:
                        break
                    file.write(file_data)
            messagebox.showinfo("Fetch", f"File {file_name} downloaded from {peer_ip}")
            peer_socket.close()
        except socket.error as e:
            messagebox.showerror("Fetch", f"Error connecting to peer: {e}")

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

    def disconnect(self):
        self.socket.send("disconnect".encode('utf-8'))
        self.socket.close()
        self.root.destroy()

    def start_peer_server(self):
        def handle_peer_client(client_socket):
            while True:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if message.startswith("GET"):
                        _, fname = message.split()
                        if os.path.isfile(fname):
                            with open(fname, 'rb') as file:
                                while True:
                                    file_data = file.read(1024)
                                    if not file_data:
                                        break
                                    client_socket.send(file_data)
                        else:
                            client_socket.send("File not found".encode('utf-8'))
                    else:
                        break
                except socket.error:
                    break
                finally:
                   client_socket.close()

        peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        peer_server_socket.bind(('0.0.0.0', self.peer_port))
        peer_server_socket.listen(5)

        while True:
            peer_client_socket, addr = peer_server_socket.accept()
            print(f"Peer connection from {addr} has been established.")
            peer_thread = threading.Thread(target=handle_peer_client, args=(peer_client_socket,))
            peer_thread.start()

# Usage Example
client = FileSharingClient("192.168.197.1", 9999)