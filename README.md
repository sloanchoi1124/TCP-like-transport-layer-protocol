Simple TCP-like transport layer protocol
Sloan Cui   xc2315

Basically implemented functions according to the requirement;
May have missed something since I'm running out of time...

Usage:
python Sender.py <filename> <remoteIP> <remote_port> <ack_port_num> <log_filename> <windowsize>
python Receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>

Design

   -Receiver.py
        Only responds to incoming segments with correct sequence number;

        If due to packet loss or reverse order on the sending path, Receiver doesn't respond and count on the Sender to resend segments after timeout;

   -Sender.py
        if window size = 1, use a stop-and-go approach: keep resending the same segment until an ACK is received

        if window size > 1, open multiple threads through threading.Timer;

        timer_handler is the callback function that handles timing and retransmission;

        All ongoing threads are stored in self.current_window; If a segment is timeout, timer_handler kills all threads for the segment and the segments after it, and resend all segments;

        If a segment receives ACK, tcp_transmission_1 cleans up the timer process of the segment;

   -TCP_standard.py
        Contains functions that help set a TCP header, pack and unpack TCP segment;
        Defines the format of a TCP segment for this program;