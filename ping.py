import subprocess
import re
import time

def ping(dest_addr,count=4,type='ipv4',timeout=1):
    type_cmd = ''
    if type != 'ipv4':
        type_cmd = '-6'
    p=subprocess.Popen("ping "+type_cmd+" -c "+str(count)+" -W "+str(timeout)+" "+dest_addr+"",
     shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  

    lost = 0        # Number of loss packets
    lost_perc = 0
    latency = []    # Delay values [MIN. MAX, AVG]
    jitter = []     # Jitter values [MAX, AVG]
    time_sent = []  # Timestamp when packet is sent
    time_recv = []  # Timestamp when packet is received
    latency_min = 0
    latency_max = 0
    latency_avg = 0
    latency_flag = 0

    result = {}
    while True:

        buff = p.stdout.readline().decode()

        if '64 bytes from' in buff:
            raw_delay = re.search('time=.*. ms',buff)
            raw_icmp_seq = re.search('icmp_seq=.*. ttl',buff)
            if raw_delay == None:
                time_recv.append(None)
                continue
            else:
                delay = float(raw_delay.group()[5:-2])
                i = int(raw_icmp_seq.group()[9:-3])-1
                cur = time.time() * 1000
                time_sent.append(cur)
                time_recv.append(cur+delay)
            # except:
            #     print("Socket error")
            #     sys.exit(1)

            # Calculate Latency:
            latency.append(time_recv[i] - time_sent[i])

            # print(time_recv[i],time_sent[i],time_recv[i] - time_sent[i])

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
        
        if 'packets transmitted,' in buff:
            raw_recv = re.search('transmitted, .*. received',buff)
            recv = int(raw_recv.group()[12:-8])
            lost = count - recv
            raw_perc = re.search('received, .*.% packet',buff)
            lost_perc = float(raw_perc.group()[9:-8])

        if 'rtt min/avg/max/mdev =' in buff:
            raw_cal = str(re.search('=.*',buff).group()[2:]).split('/')
            latency_min = float(raw_cal[0]) 
            latency_avg = float(raw_cal[1])
            latency_max = float(raw_cal[2])
            latency_flag = latency_flag+1
        
        if buff == '' and p.poll() != None:  
            break  

    if len(jitter) != 0:
        tot_jitter = jitter[len(jitter) - 1]
    else:
        tot_jitter = 'NaN'
    if latency_flag == 0:
        latency_min = 'NaN'
        latency_avg = 'NaN'
        latency_max = 'NaN'

    result['jitter'] = tot_jitter
    result['packet_loss'] = lost
    result['packet_loss_perc'] = lost_perc
    result['latency_min'] = latency_min
    result['latency_avg'] = latency_avg
    result['latency_max'] = latency_max
    result['count'] = count
    result['dst'] = dest_addr
    return result

