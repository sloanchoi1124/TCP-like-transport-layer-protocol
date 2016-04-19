import socket
import sys
import datetime
from TCP_standard import TCP_standard


class Receiver:
    def rev_and_send_ack(self):
        print "inside of rev_and_send_ack!\n"
        with open(self.filename, 'wb') as received_file:
            while True:
                packed_segment = self.rev_socket.recv(TCP_standard.PACKET_SIZE)
                unpacked_segment = TCP_standard.unpack_tcp_segment(packed_segment)
                expected_seq_no = 0

                #check corruption through checksum
                #if corrupted, continue

                #check if sequence number is correct; if not, ignore this case and continue
                if unpacked_segment.sequence_no == expected_seq_no:
                    expected_seq_no += len(unpacked_segment.data)
                    received_file.write(unpacked_segment.data)
                    #send ack to sender
                    print "about to send ackback\n"
                    print str(unpacked_segment.ack_no) + '\n'
                    self.ack_socket.sendall(str(unpacked_segment.ack_no))
                    #log into log_file at here
                else:
                    continue

                if unpacked_segment.FIN == 1:
                    break

            #if get out of this while loop, all segments must have been received
            print("Transmission successful\n")
            print("Total bytes read to " + self.filename + ': ' + str(expected_seq_no))

    def __init__(self):
        self.filename = sys.argv[1]
        self.listening_port = int(sys.argv[2])
        self.sender_IP = sys.argv[3]
        self.sender_port = int(sys.argv[4])
        self.log_filename = sys.argv[5]

        print "inside __init__ in Receiver.py\n"
        print sys.argv

        # create socket for sending ACK and recving file
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
        self.rev_and_send_ack()


if __name__ == "__main__":
    print "About to start Receiver\n"
    Receiver()
