import socket
from subprocess import Popen, STDOUT, PIPE
from threading import Thread


class ProcessOutputThread(Thread):  # OOPS
    def __init__(self, proc, conn):
        Thread.__init__(self)
        self.proc = proc
        self.conn = conn

    def run(self):
        while not self.proc.stdout.closed:
            conn.sendall(self.proc.stdout.readline())


HOST = ''
PORT = 8877

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen()
conn, addr = s.accept()
print("{} connected with back port {}".format(addr[0], addr[1]))
conn.sendall(
    "Simple Math Server developed by LAHTP \n\nGive any math expressions, and I will answer you :) \n\n$ ".encode())

p = Popen(['bc'], stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True)
output = ProcessOutputThread(p, conn)
output.start()

while not p.stdout.closed:
    data = conn.recv(1024)
    if not data:
        break
    else:
        data = data.decode()
        query = data.strip()
        if query == 'quit' or query == 'exit':
            p.communicate(query.encode(), timeout=1)
            if p.poll() is not None:
                break
        query = query + '\n'
        p.stdin.write(query.encode())
        p.stdin.flush()
s.close()
