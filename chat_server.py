import socket
from threading import Thread
import sys

server = None
CONNECTION_LIST = []
connection_binding = ("", 4321)


class Sender(Thread):
    def __init__(self, server_socket, name):
        Thread.__init__(self)
        self.name = name
        self.server_socket = server_socket

    def run(self):
        global server
        try:
            while True:
                server_message = input()

                if server_message == "shutdown":
                    print("\n\nquiting server...\n\n")
                    self.server_socket.close()
                    server.close()
                    sys.exit(0)
                elif server_message == "help":
                    print("::HELP::\n'help': get the commands\n'server shutdown': shutdown the server\n'$ls': list people "
                          "online")
                elif server_message == "$ls":
                    print("\n")
                    if len(CONNECTION_LIST) > 10:
                        print("Lots of people are here:...")
                    print("People Online(" + str(len(CONNECTION_LIST)) + "): ")
                    for client_connection in CONNECTION_LIST:
                        client_name = client_connection[1]
                        print(client_name)
                    print("SERVER.\n")
            else:
                send_text = "\n\n" + self.name + ":" + server_message + "\n\n"
                broadcast_to_clients(self.server_socket, send_text.title())
        except:
            print("\n\nquiting server...\n\n")
            self.server_socket.close()
            server.close()
            sys.exit(0)


class Receiver(Thread):
    def __init__(self, connection, name):
        Thread.__init__(self)
        self.connection = connection
        self.name = name

    def run(self):
        while self.connection.fileno() != -1:
            try:
                byte_data = self.connection.recv(1024)
                if byte_data and byte_data.decode().strip() != "quit":
                    if byte_data.decode().strip() == "help":
                        help_client(self.connection)
                    elif byte_data.decode().strip() == "$ls":
                        send_presence(self.connection)
                    else:
                        message = "\n" + self.name + ": " + byte_data.decode().strip() + "\n"
                        print(message)
                        broadcast_to_clients(self.connection, message)
                else:
                    self.connection.close()
                    information = "\n" + self.name + " left the chat.\n\n"
                    print(self.name + " left the chat.")
                    broadcast_to_clients(self.connection, information)
                    if self.connection in CONNECTION_LIST:
                        CONNECTION_LIST.remove(self.connection)
            except:
                self.connection.close()
                information = "\n" + self.name + " left the chat.\n\n"
                print(self.name + " left the chat.")
                broadcast_to_clients(self.connection, information)
                if (self.connection, self.name) in CONNECTION_LIST:
                    CONNECTION_LIST.remove((self.connection, self.name))


def broadcast_to_clients(connection, message):
    global CONNECTION_LIST
    for client_connection in CONNECTION_LIST:
        if connection != client_connection[0]:
            try:
                client_connection[0].sendall(message.encode())
            except:
                client_connection[0].close()
                if client_connection in CONNECTION_LIST:
                    CONNECTION_LIST.remove(client_connection)


def send_presence(connection):
    try:
        connection.sendall(b"\n")
        if len(CONNECTION_LIST) > 10:
            connection.sendall(b"Lots of people are here:...\n")
        connection.sendall(
            b"People Online(" + str(len(CONNECTION_LIST)).encode() + b"): \n\n")
        for client_connection in CONNECTION_LIST:
            client_name = client_connection[1]
            connection.sendall(client_name.encode() + b"\n")
        connection.sendall(b"SERVER.\n\n")
    except:
        connection.close()


def help_client(connection):
    try:
        help_text = "\n\n::HELP::\n'quit': quit the chat\n'help': list of commands\n'$ls': list people online\n"
        connection.sendall(help_text.encode() + b"\n\n")
    except:
        connection.close()


class Initiator(Thread):
    def __init__(self, connection):
        Thread.__init__(self)
        self.connection = connection

    def run(self):
        name_byte = None
        try:
            self.connection.sendall(b'\nHi, Welcome to our chat server...\nEnter \'help\' to get help\n\nYour name '
                                    b'please: ')
            name_byte = self.connection.recv(1024)
        except:
            pass
        if name_byte and name_byte.decode().strip() != "quit":
            name = name_byte.decode().strip() + \
                " @ (" + self.connection.getpeername()[0] + ")"
            CONNECTION_LIST.append((self.connection, name))
            try:
                self.connection.sendall(
                    b'\nWelcome to our chat room, ' + name_byte + b'\n')
                information = "\n" + name + " entered the chat\n\n"
                print(name + " entered the chat")
                broadcast_to_clients(self.connection, information)
            except:
                self.connection.close()
                information = "\n" + self.name + " left the chat.\n\n"
                print(self.name + " left the chat.")
                broadcast_to_clients(self.connection, information)
                if (self.connection, self.name) in CONNECTION_LIST:
                    CONNECTION_LIST.remove((self.connection, self.name))

            send_presence(self.connection)
            receive = Receiver(self.connection, name)
            receive.start()
        else:
            self.connection.close()


def start_server():
    global server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server_socket.bind(connection_binding)
    server = server_socket
    server_socket.listen(10)
    print("server started....\n")
    send = Sender(server_socket, "SERVER")
    send.start()
    while server_socket and server_socket.fileno() != -1:
        try:
            connection, address = server_socket.accept()
            initiation = Initiator(connection)
            initiation.start()
        except:
            print("server stopped.")
            return 1
    return 0


if __name__ == "__main__":
    start_server()
