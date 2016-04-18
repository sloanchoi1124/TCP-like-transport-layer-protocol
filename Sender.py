import sys
import socket
import TCP_standard
import datetime


class Sender:
    BACKLOG = 1

    def tcp_transmission(self):
        #check how does tcp work and implement it later


    def prepare_tcp_segments(self):
        with open(self.filename, "rb") as f:
            current_chunk = f.read(TCP_standard.TCP_standard.MSS)
            sequence_no = 0
            expected_ack = sequence_no + len(current_chunk)

            # when reading file in chunk, if returns an empty string, meaning that it hits eof
            while current_chunk != '':
                previous_chunk = current_chunk
                current_chunk = f.read(TCP_standard.TCP_standard.MSS)

                # hit the last chunk
                if (len(current_chunk) < TCP_standard.TCP_standard.MSS):
                    # set FIN == 1
                    current_segment = TCP_standard.TCP_standard(self.ack_port_num, self.remote_port, sequence_no,
                                                                expected_ack, 1, previous_chunk)

                else:
                    current_segment = TCP_standard.TCP_standard(self.ack_port_num, self.remote_port, sequence_no,
                                                                expected_ack, 0, previous_chunk)

                self.all_seq_no.append(sequence_no)
                self.seq_ack_dict[sequence_no] = expected_ack
                self.seq_seg_dict[sequence_no] = current_segment

                sequence_no += len(previous_chunk)
                expected_ack = sequence_no + len(current_chunk)
            self.byte_count += sequence_no

    def __init__(self):

        self.filename = sys.argv[1]
        self.remote_IP = sys.argv[2]
        self.remote_port = int(sys.argv[3])
        self.ack_port_num = int(sys.argv[4])
        self.log_filename = sys.argv[5]
        if sys.argv[6]:
            self.window_size = sys.argv[6]
        else:
            self.window_size = 1

        self.byte_count = 0

        # establish a connection here
        # send socket is UDP, receive ack socket is TCP
        try:
            self.send_file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as e:
            print('Failed to create send socket (UDP): %s' % e)
            sys.exit(1)

        # now can send stuff to remote IP

        try:
            self.receive_ack_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.receive_ack_sock.bind(('localhost', self.ack_port_num))
            self.receive_ack_sock.listen(self.BACKLOG)
            self.ack_connection, self.ack_addr = self.receive_ack_sock.accept()

        except socket.error as e:
            print('Failed to create receive socket (TCP): %s' % e)
            sys.exit(1)

        # at this point, the two sockets should be ready
        # all_seq_no keeps an in order list of sequence # of each TCP segment
        self.all_seq_no = []
        # <sequence_no> <ack_no>
        self.seq_ack_dict = {}
        # <sequence_no> <TCP segment>
        self.seq_seg_dict = {}

        # read file and store them in the above structures
        # for convenience, read the whole file in once
        # note that segments in seq_seg_dict are not packed; need to pack them into a TCP segments during transmission

        try:
            self.prepare_tcp_segments()
        except:
            print("read file error")

        # send stuff to receiver
