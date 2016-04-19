import socket
import sys
from TCP_standard import TCP_standard
import datetime


class Receiver:
    def log_data(self, timestamp, seq_no, ack_no, FIN):
        with open(self.log_filename, "a") as logfile:

            logfile.write('Timestamp: ' + str(timestamp) + ', ' \
                         + 'Source: ' + str(self.IP_addr) + ':' + str(self.listening_port) + ', ' \
                         + 'Destination: ' + str(self.sender_IP) + ':' + str(self.sender_port) + ', ' \
                         + 'Sequence number: ' + str(seq_no) + ', ' \
                         + 'ACK number: ' + str(ack_no) + ', ' \
                         + 'FIN: ' + str(FIN) + '\n')

    def rev_and_send_ack_1(self):
        with open(self.filename, 'wb') as output:
            packed_segment = self.rev_socket.recv(TCP_standard.PACKET_SIZE)

            unpacked_segment = TCP_standard.unpack_tcp_segment(packed_segment)
            print "received seq# %d\n" % unpacked_segment.sequence_no
            next_expected_sequence_no = 0

            while unpacked_segment.FIN == 0:
                packet_valid = True
                if TCP_standard.is_corrupted(unpacked_segment):
                    packet_valid = False

                if unpacked_segment.sequence_no != next_expected_sequence_no:
                    packet_valid = False

                if packet_valid:
                    next_expected_sequence_no += len(unpacked_segment.data)
                    output.write(unpacked_segment.data)
                    timestamp = datetime.datetime.now()
                    self.log_data(timestamp, unpacked_segment.sequence_no, unpacked_segment.ack_no, unpacked_segment.FIN)

                    print "will send ack %d\n" % unpacked_segment.ack_no
                    correct_size = str(unpacked_segment.ack_no).ljust(32)
                    self.ack_socket.sendall(correct_size)
                packed_segment = self.rev_socket.recv(TCP_standard.PACKET_SIZE)
                unpacked_segment = TCP_standard.unpack_tcp_segment(packed_segment)
                print "received seq# %d\n" % unpacked_segment.sequence_no



            output.write(unpacked_segment.data.strip())
            print "will send ack %s\n" % unpacked_segment.ack_no
            self.ack_socket.sendall(str(unpacked_segment.ack_no))
            next_expected_sequence_no += len(unpacked_segment.data.strip())

            print 'Transmission successful. '
            print 'Total bytes read to ' + self.filename + ': ' + str(next_expected_sequence_no)



    def __init__(self):
        self.filename = sys.argv[1]
        self.listening_port = int(sys.argv[2])
        self.sender_IP = sys.argv[3]
        self.sender_port = int(sys.argv[4])
        self.log_filename = sys.argv[5]
        self.IP_addr = socket.gethostbyname('localhost')
        print self.IP_addr

        print "inside __init__ in Receiver.py\n"
        print sys.argv

        # create socket for sending ACK and recving file

        #detect if it's IPv6 or IPv4
        try:
            self.ack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ack_socket.connect((self.sender_IP, self.sender_port))
        except socket.error as e:
            print('Failed to create ack socket(TCP): %s' % e)
            sys.exit(1)

        try:
            self.rev_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rev_socket.bind(('localhost', self.listening_port))
        except socket.error as e:
            print('Failed to create rev socket(UDP): %s' % e)

            # now take care of receiving segments from sender
        self.rev_and_send_ack_1()


if __name__ == "__main__":
    print "About to start Receiver\n"
    Receiver()
