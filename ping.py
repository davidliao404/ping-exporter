#!/usr/bin/env python


import os, sys, socket, struct, select, time, datetime, getopt

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.


def checksum(source_string):
    """
    I'm not too confident that this is right but testing seems
    to suggest that it gives the same answers as in_cksum in ping.c
    """
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = source_string[count + 1]*256 + source_string[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff # Necessary?
        count = count + 2

    if countTo<len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff # Necessary?

    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(my_socket, ID, timeout):
    """
    receive the ping from the socket.
    """
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([my_socket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return

        timeReceived = time.time()
        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return


def send_one_ping(my_socket, dest_addr, ID):
    """
    Send one ping to the given >dest_addr<.
    """
    dest_addr  =  socket.gethostbyname(dest_addr)

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", time.time()) + str.encode(data)
    # data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1


def do_one(src_addr, dest_addr, timeout,protocol_version='ipv4'):
    """
    Returns either the delay (in seconds) or none on timeout.
    """
    
    if protocol_version == 'ipv6':
        ## ipv6
        icmp = socket.getprotobyname("ipv6-icmp")
    else:
        ## ipv4
        icmp = socket.getprotobyname("icmp")
    
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    my_ID = os.getpid() & 0xFFFF
    my_socket.bind((src_addr,0))
    send_one_ping(my_socket, dest_addr, my_ID)
    delay = receive_one_ping(my_socket, my_ID, timeout)

    my_socket.close()
    return delay


def verbose_ping(src_addr, dest_addr, timeout = 2, count = 4):
    """
    Send >count< ping to >dest_addr< with the given >timeout< and display
    the result.
    """
    for i in range(count):
        print ("ping %s..." % dest_addr),
        try:
            delay  =  do_one(src_addr, dest_addr, timeout)
        except socket.gaierror as e:
            print ("failed. (socket error: '%s')" % e[1])
            break

        if delay  ==  None:
            print ("failed. (timeout within %ssec.)" % timeout)
        else:
            delay  =  delay * 1000
            print ("get ping in %0.4fms" % delay)

def ping(count=10,timeout=2,src_addr='',src_name='src',dest_addr = '8.8.8.8',
    dest_name = 'dst',protocol_version='ipv4'):

    lost = 0        # Number of loss packets
    mos = 0         # Mean Opinion Score
    latency = []    # Delay values [MIN. MAX, AVG]
    jitter = []     # Jitter values [MAX, AVG]
    time_sent = []  # Timestamp when packet is sent
    time_recv = []  # Timestamp when packet is received


    for i in range(0, count):
        time_sent.append(int(round(time.time() * 1000)))
        d = do_one(src_addr, dest_addr, timeout,protocol_version)
        if d == None:
            lost = lost + 1
            time_recv.append(None)
            continue
        else:
            time_recv.append(int(round(time.time() * 1000)))

        # Calculate Latency:
        latency.append(time_recv[i] - time_sent[i])

        # Calculate Jitter with the previous packet
        # http://toncar.cz/Tutorials/VoIP/VoIP_Basics_Jitter.html
        if len(jitter) == 0:
            # First packet received, Jitter = 0
            jitter.append(0)
        else:
            # Find previous received packet:
            for h in reversed(range(0, i)):
                if time_recv[h] != None:
                    break
            # Calculate difference of relative transit times:
            drtt = (time_recv[i] - time_recv[h]) - (time_sent[i] - time_sent[h])
            jitter.append(jitter[len(jitter) - 1] + (abs(drtt) - jitter[len(jitter) - 1]) / float(16))

    # Calculating MOS
    if len(latency) > 0:
        EffectiveLatency = sum(latency) / len(latency) + max(jitter) * 2 + 10
        if EffectiveLatency < 160:
           R = 93.2 - (EffectiveLatency / 40)
        else:
            R = 93.2 - (EffectiveLatency - 120) / 10
            # Now, let's deduct 2.5 R values per percentage of packet loss
            R = R - (lost * 2.5)
            # Convert the R into an MOS value.(this is a known formula)
        mos = 1 + (0.035) * R + (.000007) * R * (R-60) * (100-R)

    # Setting values (timeout, lost and mos are already calculated)
    lost_perc = lost / float(count) * 100
    if len(latency) > 0:
        min_latency = min(latency)
        max_latency = max(latency)
        avg_latency = sum(latency) / len(latency)
    else:
        min_latency = 'NaN'
        max_latency = 'NaN'
        avg_latency = 'NaN'
    if len(jitter) != 0:
        tot_jitter = jitter[len(jitter) - 1]
    else:
        tot_jitter = 'NaN'

    result = {}
    result['packet_loss'] = lost
    result['packet_loss_perc'] = lost_perc
    result['jitter'] = tot_jitter
    result['latency_min'] = min_latency
    result['latency_max'] = max_latency
    result['latency_avg'] = avg_latency
    result['MOS'] = mos
    result['count'] = count
    result['src'] = src_addr
    result['dst'] = dest_addr
    return result