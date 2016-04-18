import sys
import struct


# note that this is not the exact tcp standard
# incldue helper function to pack/unpack data into TCP segments
class TCP_standard:
    HEADER_SIZE = 20
    MSS = 556
    # H -- unsigned short I--unsigned int b--signed char  s--char[]
    # TCP header includes: source port (2 bytes), dest port (2 bytes), sequence number (4 bytes), ack number (4 bytes)
    # header length (2 bytes), FIN(1 byte), ACK(1 byte), checksum(2 bytes), data
    PACKET_SIZE = HEADER_SIZE + MSS
    # note that packet size might need to be further adjusted

    # is this the correct format for header?
    # suppose this is the correct format of header for now
    HEADER_FORMAT = 'HHIIHbb2s ' + str(MSS) + 's'

    def pack_tcp_segment(self):
        #need to update checksum later
        checksum = ''
        data_padding = self.MSS - len(self.data)
        self.data += ' ' * data_padding

        return struct.pack(self.HEADER_FORMAT,
                           self.source_port, self.dest_port,
                           self.sequence_no, self.ack_no,
                           self.HEADER_SIZE, self.FIN, self.ACK,
                           str(checksum), str(self.data))

    def unpack_tcp_segment(self, packed_segment):
        (self.source_port, self.dest_port, self.sequence_no,
         self.ack_no, header_size, self.FIN, self.ACK, self.checksum,
         self.data) = struct.unpack(self.HEADER_FORMAT, packed_segment)
        return self

    def __init__(self, source_port, dest_port, sequence_no, ack_no, FIN, data):
        self.source_port = source_port
        self.dest_port = dest_port
        self.sequence_no = sequence_no
        self.ack_no = ack_no
        self.FIN = FIN
        self.data = data
