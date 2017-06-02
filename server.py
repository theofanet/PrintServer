import socket
import select
import atexit
import base64
import json
import os


class Client(object):
    _ip = ''
    _socket = False
    _connexion = False
    _token = False

    def __init__(self, connexion, soc):
        self._ip = ''
        self._connexion = connexion
        self._socket = soc

    def getSocket(self):
        return self._socket

    def receive(self):
        ndata = ""
        data = "DATABLOCK"
        while len(data):
            try:
                data = self._socket.recv(1024)
                if not data:
                    break
                ndata = ndata + data
            except socket.error:
                data = ""
                continue

        decode = base64.b64decode(ndata)
        print(decode)
        return json.loads(decode)


class Server(object):
    _hostname = ""
    _port = 0
    _max_listen = 1
    _connexion = False
    _quite = False
    _closed = False
    _connected_sockets = []
    _clients = {}

    def __init__(self, hostname='', port=5555, max_listen = 5):
        self._hostname   = hostname
        self._port       = port
        self._max_listen = max_listen

    def start(self):
        self._connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connexion.bind((self._hostname, self._port))
        self._connexion.listen(self._max_listen)

        print("#############################################################")
        print("# Server listening")
        print("# Host : {0}".format(self._hostname))
        print("# Port : {0}".format(self._port))
        print("#############################################################")

    def close(self):
        for c in self._connected_sockets:
            c.close()
        self._connexion.close()
        self._closed = True

    def isClosed(self):
        return self._closed

    def run(self):
        while not self._quite:
            waiting_connexions, wlist, xlist = select.select([self._connexion], [], [], 0.05)

            for co in waiting_connexions:
                client_socket, connexion_info = co.accept()
                client_socket.setblocking(False)
                new_client = Client(self._connexion, client_socket)
                self._connected_sockets.append(client_socket)
                self._clients[client_socket] = new_client
                print("New connexion")

            try:
                clients_to_read, wlist, xlist = select.select(self._connected_sockets, [], [], 0.05)
            except select.error:
                pass
            else:
                for c in clients_to_read:
                    if c in self._clients:
                        data_raw = self._clients[c].receive()

                        f = open("data.d", "w")
                        f.write(base64.b64decode(data_raw["pdf_data"]))
                        f.close()

                        os.system("lp -d {0} ./data.d".format(data_raw["printer_name"]))
                        os.remove("data.d")

                        self._connected_sockets.remove(c)
                        del self._clients[c]
                        c.close()

        self.close()


def exit_handler(server_to_close):
    if not server_to_close.isClosed():
        server_to_close.close()
        print("Server closed safely")


if __name__ == "__main__":
    server = Server('', 2233)
    atexit.register(exit_handler, server)
    server.start()
    server.run()
