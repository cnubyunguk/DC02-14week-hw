import socket
import os
import sys
import time
import struct

def ip2int(addr):
    return [int(x) for x in addr.split('.')]
    
def checksum(data):
    ret = 0
    data_len = len(data)
    
    # If the number of data is odd, add one more byte
    if (len(data) % 2):
        data_len += 1
        data += struct.pack('!B', 0)
    
    for i in range(0, data_len, 2):
        ret += int.from_bytes(data[i:i+2], "big")
        
    ret = (ret >> 16) + (ret & 0xFFFF)
    return ~ret & 0xFFFF
    
def create_packet(data):
    src_ip = ip_addr
    src_ip = struct.pack('!4B', *ip2int(src_ip))
 
    dst_ip = client_addr[0]
    dst_ip = struct.pack('!4B', *ip2int(dst_ip))
    
    zero = 0
    protocol = socket.IPPROTO_UDP
    src_port = port
    dst_port = client_addr[1]
    
    udp_len = 8 + len(data)
    pseudo_header = src_ip + dst_ip + struct.pack('!BBH', zero, protocol, udp_len)
    udp_header = struct.pack('!4H', src_port, dst_port, udp_len, 0)
    chksum = checksum(pseudo_header + udp_header + data)
    chksum_header = struct.pack('!4H', src_port, dst_port, udp_len, chksum)
    return pseudo_header + chksum_header + data

def sender_send():
    file_name = 'speech_script.txt'
    file_size = os.stat(file_name).st_size
    print("file size: {0}bytes".format(file_size))
    
    count = file_size % buf_size == 0 and int(file_size / buf_size) or int(file_size / buf_size) + 1
    s.sendto(create_packet(str(count).encode('utf-8')), client_addr)
    
    s.setblocking(0)
    
    data_buffer = [None] * count
    timeout = 0.5
    timer = time.time()
    send_base = 0
    next_seq = 0
    window_size = 3
    send_idx = 0
    inital_cnt = count
    f = open(file_name, "rb")
    while(True):
        try:
            ack, addr = s.recvfrom(4096)
            ack_resp = ack.decode('utf-8').split()
            recv_seq = int(ack_resp[1])
            if ack_resp[0] == 'ACK':
                print('received ACK {0}'.format(recv_seq))
                send_base = recv_seq + 1
                count -= 1
                if count <= 0: # if sent all file datas, escape loop
                    break
            else: # if received NAK
                print('received NAK {0}. resending room in window'.format(recv_seq))
                for i in range(recv_seq, next_seq):
                    s.sendto(struct.pack('!B', i) + create_packet(data_buffer[i]), client_addr)
                    print('\tresending data index {0}...'.format(i))
            timer = time.time()
        except socket.error:
            pass
            
        if time.time() - timer > timeout: #if timer expired
            print('seq {0} timer expired. resending room in window'.format(send_base))
            for i in range(send_base, next_seq):
                s.sendto(struct.pack('!B', i) + create_packet(data_buffer[i]), client_addr)
                print('\tresending data index {0}...'.format(i))
            timer = time.time()
        elif next_seq < inital_cnt and next_seq < send_base + window_size:
            data = f.read(buf_size)
                
            packet = struct.pack('!B', next_seq) + create_packet(data)
            s.sendto(packet, client_addr)
            print('sending data index: {0}'.format(next_seq))
            
            data_buffer[next_seq] = data
            next_seq = next_seq + 1
            
        
    print("sent all the files normally!")

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("please pass port number")
        sys.exit()
    
    print('It was successfully entered. Let\'s move on {0}'.format(sys.argv[1]))

    ip_addr = "127.0.0.1"
    port = int(sys.argv[1])
    buf_size = 1003 # 21 bytes of 1024 bytes consist of sequence + psuedo header + udp_header

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((ip_addr, port))
    except socket.error:
        print("failed to create socket")
        sys.exit()

    print('successfully created socket')
    print('waiting for client now...')
    
    try:
        data, client_addr = s.recvfrom(4096)
    except ConnectionResetError:
        print("error. port number not matching.")
        sys.exit()
    
    if data.decode('utf-8') == '201904243':
        sender_send()
    else:
        print('student number not matching')
        
    sys.exit()
