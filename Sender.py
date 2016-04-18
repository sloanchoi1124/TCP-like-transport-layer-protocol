import sys
import socket
import TCP_standard
import multiprocessing
import time



class Sender:
    BACKLOG = 1
    INITIAL_TIMEOUT = 1
    ACK_BUFF = 16


    #returns the sequence number of the last segment that has received ACK from the Receiver
    #return -1 if no segment has received ACK so far
    def last_acked_seq(self):
        last_acked = -1
        for seq_no_temp in self.all_seq_no:
            if self.already_acked[seq_no_temp]:
                last_acked = seq_no_temp
                continue
            else:
                break
        return last_acked

    #returns the number of segments that has not yet received ACK
    def remaining_segments(self):
        count = 0
        for seq_no_temp in self.all_seq_no:
            if not self.already_acked[seq_no_temp]:
                count += 1
        return count


    def tcp_transmission(self):
        # initialize the setting
        # if window_size > total number of packets, send them all
        if self.window_size >= len(self.all_seq_no):
            all_processes = []
            for seq_no_temp in self.all_seq_no:
                # create a process to send segment and wait for ACK of that segment
                p = multiprocessing.Process(target=self.send_and_recv,
                                            args=(self.seq_seg_dict[seq_no_temp], seq_no_temp))
                all_processes.append(p)
                p.start()

            # wait until every process is finished; report success here
            for process_temp in all_processes:
                process_temp.join()

        # window_size < total number of packets; need move window
        # important to notice: when to join?

        else:
            #make current_window_processes as a list of tuples;
            #(seq#, process)
            current_window_processes = []

            while True:
                #first check if all segments have been acked; if so, report success
                if self.remaining_segments() == 0:
                    print 'Success'
                    break

                #second, check if there's still need to start new process to send data
                if self.already_sent[self.all_seq_no[-1]]:
                    if len(current_window_processes) > 0:
                        #at least wait until an ACK has been received
                        current_window_processes[0][1].join()
                    continue

                if len(current_window_processes) < self.window_size:
                    #do something here
                    counter = self.window_size - len(current_window_processes)
                    # if segments that are not sent are less than counter, push them all
                    # else, find the next <counter> segments and open new processes

                #   remove processes that are dead
                #   if a process is dead, then it must have already received ack from the Receiver;
                #   note that at least process 1 is finished!
                for temp_tuple in current_window_processes:
                    if not temp_tuple[1].is_alive():
                        current_window_processes.remove(temp_tuple)
                continue



    # may need to use select here; only respond when there's new info available
    # check later; maybe it's not a problem at all, since it runs on a separate process...
    # send_and_recv sends segment and wait for ACK from Receiver; if timeout, then it resends segment
    # note that acks come in order; if packet 1, 2, 3 sent, 2 lost, it's impossible to receive ack from 3
    def send_and_recv(self, unpacked_segment, seq_no):
        # this function sends a TCP segment and wait for response
        # it is the receiver's responsibility to send ACK in order; receiver never send ack in wrong order
        # plus, receiver sends ack back using tcp;
        start_time = time.clock()
        print "--sending segment-- sequence number = %d\n", seq_no
        packed_segment = TCP_standard.TCP_standard.pack_tcp_segment(unpacked_segment)
        self.send_file_sock.sendto(packed_segment, (self.remote_IP, self.remote_port))
        try:
            self.receive_ack_sock.settimeout(self.timeout_interval)
            # keep reading from socket;
            while True:
                ack_no = self.receive_ack_sock.recv(self.ACK_BUFF)
                if ack_no == self.seq_ack_dict[seq_no]:
                    # receive ack, update dictionary
                    self.already_acked[seq_no] = True
                    break
                else:
                    # if received ack of previous packets, reset timeout, and keep listening to stuff

                    # important!!! reset timeout here!!!
                    self.receive_ack_sock.settimeout(self.timeout_interval - (time.clock() - start_time))
                    continue
        except socket.timeout:
            # retransmit immediately
            self.send_and_recv(unpacked_segment)

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
                # this should include the case where the file is 0 bytes
                if len(current_chunk) < TCP_standard.TCP_standard.MSS:
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

        self.timeout_interval = self.INITIAL_TIMEOUT
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

        # this dictionary keeps track of whether a segment is already acked
        self.already_acked = {}
        # this dictionary keeps track of whether a segment is already sent
        self.already_sent = {}

        # read file and store them in the above structures
        # for convenience, read the whole file in once
        # note that segments in seq_seg_dict are not packed; need to pack them into a TCP segments during transmission

        try:
            self.prepare_tcp_segments()
        except:
            print("read file error")

        # before file transmission, nothing is acked
        for seq_no_temp in self.all_seq_no:
            self.already_acked[seq_no_temp] = False

        for seq_no_temp in self.all_seq_no:
            self.already_sent[seq_no_temp] = False
