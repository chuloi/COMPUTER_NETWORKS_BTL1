import socket
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

class FileSharingServer:
    def __init__(self):
        self.client_data = {}  # Stores client IP and shared files
        self.server_running = True

        self.create_listening_server()

        self.root = tk.Tk()
        self.root.title("File Sharing Server")
        self.create_gui()

        threading.Thread(target=self.receive_messages_in_a_new_thread, daemon=True).start()
        threading.Thread(target=self.run_command_shell, daemon=True).start()

    def create_gui(self):
        self.log_text = scrolledtext.ScrolledText(self.root, width=50, height=15, wrap=tk.WORD)
        self.log_text.pack(padx=15, pady=15)

        self.command_entry = tk.Entry(self.root, width=30)
        self.command_entry.pack(pady=10)

        self.send_button = tk.Button(self.root, text="Send Command", command=self.send_command)
        self.send_button.pack()

    def send_command(self):
        command = self.command_entry.get()
        self.log_message(f"Command: {command}")
        self.handle_command(command)
        self.command_entry.delete(0, tk.END)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def create_listening_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        local_port = 9999
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((local_ip, local_port))
        print(f"Listening for incoming messages on {local_ip}:{local_port}")
        self.server_socket.listen(5)

    def handle_command(self, command):
        if command.startswith("discover"):
            _, hostname = command.split()
            self.discover_files(hostname)
        elif command.startswith("ping"):
            _, hostname = command.split()
            self.ping_client(hostname)
        elif command == "exit":
            self.log_message("Shutting down server...")
            self.server_running = False
            self.root.quit()
        else:
            self.log_message("Unknown command")

    def run_command_shell(self):
        while self.server_running:
            time.sleep(1)

    def handle_client(self, client_socket, addr):
        self.log_message(f"Connection from {addr} has been established.")
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                command, data = self.parse_client_message(message)
                if command == 'publish':
                    self.publish_files(client_socket, data)
                elif command == 'fetch':
                    self.send_file_sources(client_socket, data)

            except socket.error:
                break
        client_socket.close()

    def parse_client_message(self, message):
        parts = message.split()
        return parts[0], parts[1:]

    def publish_files(self, client_socket, file_list):
        client_address = client_socket.getpeername()[0]
        self.client_data[client_address] = file_list
        client_socket.send("Files published successfully".encode('utf-8'))

    def send_file_sources(self, client_socket, data):
        file_name = data[0]
        sources = [ip for ip, files in self.client_data.items() if file_name in files]
        response = ' '.join(sources)
        client_socket.send(response.encode('utf-8'))

    def receive_messages_in_a_new_thread(self):
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                print(f"An error occurred: {e}")

    def discover_files(self, hostname):
        for client_ip, files in self.client_data.items():
            if hostname == client_ip:  # Assuming hostname is the IP of the client
                self.log_message(f"Files for {hostname}: {files}")
                break
        else:
            self.log_message(f"No files found for {hostname}")

    def ping_client(self, hostname):
        if hostname in self.client_data or any(hostname in ip for ip in self.client_data):
            self.log_message(f"{hostname} is active")
        else:
            self.log_message(f"{hostname} is not active or not connected")


# Usage
server = FileSharingServer()
server.root.mainloop()  # Start the Tkinter main loop
