import sys
import socket
import TCP_standard
import time
import select
from threading import Timer
import datetime


class Sender:
    BACKLOG = 1
    INITIAL_TIMEOUT = 100
    ACK_BUFF = 16

    INITIAL_RTT = 1
    RTT_ALPHA = 0.125
    RTT_BETA = 0.25

    def log_data(self, timestamp, sequence_no, ack_no, FIN):
        #print 'inside log_data\n'
        with open(self.log_filename, 'a') as logfile:
            logfile.write('Timestamp: ' + str(timestamp) + ', ' \
                          + 'Source: ' + str(self.IP_addr) + ':' + str(self.ack_port_num) + ', ' \
                          + 'Destination: ' + str(self.remote_IP) + ':' + str(self.remote_port) + ', ' \
                          + 'Sequence number: ' + str(sequence_no) + ', ' \
                          + 'ACK number: ' + str(ack_no) + ', ' \
                          + 'FIN: ' + str(FIN) + ', ' \
                          + 'Estimated RTT: ' + str(self.estimated_RTT) + '\n')

    def tcp_transmission_1(self):
        # this is a stable version for window size = 1
        if int(self.window_size) == 1:
            print "Handling window_size = 1"
            for seq_no_temp in self.all_seq_no:
                self.send_and_receive(self.seq_seg_dict[seq_no_temp])

        # when window size > 1
        elif int(self.window_size) > 1:
            if int(self.window_size) >= len(self.all_seq_no):
                for seq_no_temp in self.all_seq_no:
                    self.send_segment(self.seq_seg_dict[seq_no_temp])

                # after sending, wait for response
                expected_ack = self.seq_ack_dict[self.all_seq_no[-1]]
                print "expected %d\n" % expected_ack
                while 1:
                    socket_list = [self.ack_connection]

                    try:
                        read_socket, write_socket, error_socket = select.select(socket_list, [], [])
                        # every ack is packed in a 32-byte string, passed into socket...
                        # should be enough for now...
                        data = read_socket[0].recv(32)
                        if not data:
                            print 'no data!!! \n'
                            break
                        else:
                            print data
                            if int(data) == expected_ack:
                                print "Success!\n"
                                break
                    except socket.error:
                        print "socket error\n"
            else:
                # current_window is a list of tuple (seq#, timer)
                # first of all, put n segments on window
                print 'line 65\n'
                i = 0
                while i < int(self.window_size):
                    seq_no_temp = self.all_seq_no[i]
                    self.send_segment(self.seq_seg_dict[seq_no_temp])
                    try:
                        timer = Timer(self.timeout_interval, self.timeout_handler, [seq_no_temp])
                        timer.start()
                        self.current_window.append((seq_no_temp, timer))
                    except:
                        print "timer setting error!!"

                    i += 1

                print 'line 79\n'
                print self.current_window
                # receive
                while True:

                    socket_list = [self.ack_connection]
                    try:
                        read_socket, write_socket, error_socket = select.select(socket_list, [], [])
                        data = read_socket[0].recv(32)
                        # if data matches something on current window, get rid of that and move forward
                        if int(data) == self.seq_ack_dict[self.all_seq_no[-1]]:
                            # kill all threads that are still alive
                            for temp in self.current_window:
                                temp[1].cancel()
                            print "Success at line 122!\n"
                            break

                        self.current_window[0][1].cancel()
                        self.current_window = self.current_window[1:]
                        # stop the clock here
                        self.remaining_seq.pop(0)
                        print 'line 136'

                        # add the next element in remaining seq
                        if len(self.remaining_seq) > 0:
                            seq_no_temp = self.remaining_seq[0]
                            self.send_segment(self.seq_seg_dict[seq_no_temp])
                            timer = Timer(self.INITIAL_TIMEOUT, self.timeout_handler, [seq_no_temp])
                            timer.start()
                            self.current_window.append((seq_no_temp, timer))
                        else:
                            for temp in self.current_window:
                                temp[1].cancel()
                            print 'line 136\n'
                            print 'success at line 141!\n'
                            break

                    except socket.error:
                        print "socket error"
                        sys.exit(1)

        else:
            print "invalid window size\n"
            sys.exit(1)

    def timeout_handler(self, seq_no):
        # need to lock this part of the code!!!! because will be changing self.current_window
        print "inside timeout handler\n"
        seq_index = 0
        for temp in self.current_window:
            if temp[0] == seq_no:
                seq_index = temp[0]
        # cancel the rest of the timer
        for temp in self.current_window[seq_index:]:
            # kill the timer process there
            temp[1].cancel()

        self.current_window = self.current_window[:seq_index]
        available_slots = int(self.window_size) - len(self.current_window)
        i = 0
        while i < available_slots:
            seq_no_temp = self.remaining_seq[i]
            timer = Timer(self.INITIAL_TIMEOUT, self.timeout_handler, [seq_no_temp])
            timer.start()
            self.current_window.append((seq_no_temp, timer))

            # must kill all timer process!!!!!!!!

    # this function only send segment
    def send_segment(self, unpacked_segment):
        print 'inside send_segment\n'
        packed_segment = TCP_standard.TCP_standard.pack_tcp_segment(unpacked_segment)
        try:
            self.send_file_sock.sendto(packed_segment, (self.remote_IP, self.remote_port))
            timestamp = datetime.datetime.now()
            self.log_data(timestamp, unpacked_segment.sequence_no, unpacked_segment.ack_no, unpacked_segment.FIN)
        except socket.error:
            print "Error when socket trying to send stuff...\n"
            pass

    # this is a special case!!!!
    # this function handles the situation when window size = 1
    def send_and_receive(self, unpacked_segment):
        print "sent seq# %d\n" % unpacked_segment.sequence_no
        packed_segment = TCP_standard.TCP_standard.pack_tcp_segment(unpacked_segment)
        try:
            self.send_file_sock.sendto(packed_segment, (self.remote_IP, self.remote_port))
            timestamp = datetime.datetime.now()
            self.log_data(timestamp, unpacked_segment.sequence_no, unpacked_segment.ack_no, unpacked_segment.FIN)

        except socket.error:

            print "Error when socket trying to send stuff...\n"
        try:
            self.ack_connection.settimeout(self.timeout_interval)
            ack_no = self.ack_connection.recv(32)
            print ack_no + '\n'
        except socket.timeout:
            self.send_and_receive(unpacked_segment)

    def prepare_tcp_segments_1(self):
        with open(self.filename, "rb") as f:
            seq_no = 0
            # need to be able to handle reading empty file!
            while True:
                current_chunk = f.read(TCP_standard.TCP_standard.MSS)
                expected_ack = seq_no + len(current_chunk)

                if current_chunk == '':
                    # meaning that this is the end of file...
                    print "reach end of file!"
                    break
                if len(current_chunk) < TCP_standard.TCP_standard.MSS:
                    current_segment = TCP_standard.TCP_standard(self.ack_port_num, self.remote_port, seq_no,
                                                                expected_ack, 1, current_chunk)

                else:
                    current_segment = TCP_standard.TCP_standard(self.ack_port_num, self.remote_port, seq_no,
                                                                expected_ack, 0, current_chunk)

                self.all_seq_no.append(seq_no)
                self.seq_ack_dict[seq_no] = expected_ack
                self.seq_seg_dict[seq_no] = current_segment
                print "Message from prepare tcp segment"
                print "seq# = %d ack = %d FIN=%d data = %s\n" % (
                    current_segment.sequence_no, current_segment.ack_no, current_segment.FIN, current_segment.data)

                seq_no += len(current_chunk)

    # helper functions regarding updating RTT and stuff
    def update_timeout_and_RTT(self, sample_RTT):
        self.update_deviation_RTT(sample_RTT)
        self.update_estimated_RTT(sample_RTT)
        self.update_tiemout_interval(sample_RTT)

        # tracks how long packet transmission should take

    def update_estimated_RTT(self, sample_RTT):
        # first packet transmitted
        if self.estimated_RTT == self.INITIAL_RTT:
            self.estimated_RTT = sample_RTT
        else:  # formula on page 239
            self.estimated_RTT = (1 - self.RTT_ALPHA) * self.estimated_RTT \
                                 + self.RTT_ALPHA * sample_RTT

            # tracks the variability of RTT

    def update_deviation_RTT(self, sample_RTT):
        self.deviation_RTT = (1 - self.RTT_BETA) * self.deviation_RTT + \
                             self.RTT_BETA * abs(sample_RTT - self.estimated_RTT)

    def update_tiemout_interval(self, sample_RTT):
        self.timeout_interval = self.estimated_RTT + 4 * self.deviation_RTT

    def __init__(self):

        # check argv format here!!!
        print sys.argv

        self.filename = sys.argv[1]
        self.remote_IP = sys.argv[2]
        self.remote_port = int(sys.argv[3])
        self.ack_port_num = int(sys.argv[4])
        self.log_filename = sys.argv[5]
        if len(sys.argv) == 7:
            self.window_size = sys.argv[6]
        else:
            self.window_size = 1

        self.IP_addr = socket.gethostbyname('localhost')

        self.byte_count = 0

        self.timeout_interval = self.INITIAL_TIMEOUT
        # establish a connection here
        # send socket is UDP, receive ack socket is TCP
        try:
            self.send_file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print "send_file_sock created successfully\n"
        except socket.error as e:
            print('Failed to create send socket (UDP): %s' % e)
            sys.exit(1)

        # now can send stuff to remote IP

        try:
            self.receive_ack_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.receive_ack_sock.bind(('localhost', self.ack_port_num))
            self.receive_ack_sock.listen(self.BACKLOG)
            self.ack_connection, self.ack_addr = self.receive_ack_sock.accept()
            print "receive_ack_sock created successfully\n"

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

        # this dictionary keeps track of whether a segment is already acked
        self.already_acked = {}
        # this dictionary keeps track of whether a segment is already sent
        self.already_sent = {}

        # read file and store them in the above structures
        # for convenience, read the whole file in once
        # note that segments in seq_seg_dict are not packed; need to pack them into a TCP segments during transmission


        self.estimated_RTT = self.INITIAL_RTT
        self.timeout_interval = self.INITIAL_TIMEOUT
        self.deviation_RTT = 0

        try:
            self.prepare_tcp_segments_1()
        except:
            print("read file error")
            exit()

        print "--- printing all_seq_no ---\n"
        print self.all_seq_no

        # start sending stuff
        self.current_window = []
        self.remaining_seq = self.all_seq_no
        try:
            self.tcp_transmission_1()
        except:
            print("tcp_transmission_1() error somewhere")
            sys.exit(1)

        sys.exit()
        # close socket afterwards


if __name__ == "__main__":
    print "About to start Sender\n"
    Sender()
